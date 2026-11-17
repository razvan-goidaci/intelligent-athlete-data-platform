# Bronze layer design

## Purpose

This document defines the design of the Bronze layer, which holds the raw data extracted from the Garmin export. Bronze does not modify or clean the source data.

## Scope

This design covers the Garmin export ZIP. Other sources, such as an API, are out of scope and would need their own lineage columns.

The platform runs locally for a single athlete, so Bronze has no user or athlete column.

## Decision: how FIT data is split into tables

### Problem

Every row in a table needs to have the same meaning, so that the Silver layer can query it reliably.

### Options

**Option 1: one table per FIT file type**

One row is one message, of any message type, from a FIT file of that file type.

Trade-offs:

- Messages with many fields add columns that stay empty for the other messages in the same file.
- Rows in the same table mean different things. For example, `record` messages are frequent timestamped sensor readings, while a `session` message is a short summary of the whole activity's averages and results.

**Option 2: one table per FIT message type**

One row is one message of that message type, from any FIT file. Each field of the message is a column.

Trade-offs:

- There are more tables, so combining data across message types costs more.

### Decision

Option 2.

### Reasoning

One table per message type makes the schema easier to work with in the Silver layer, because each table holds only one kind of message instead of unrelated messages mixed together.

## Decision: which data enters Bronze

Bronze loads only the retained source scope defined in `docs/data_dictionary.md`, section 2.

- **Why:** the platform has a defined scope, and loading data outside it adds tables nobody uses. Bronze filters which sources it loads, but it never changes the values it loads.
- **Trade-off:** if the scope widens later, the new sources have to be ingested again from the export ZIP. Nothing is lost, because the ZIP is kept.

## FIT tables

Each table is named after the message name the parser reports. Bronze does not rename messages, including `unknown_*` messages in the numeric file types, because a meaningful name would be an interpretation. Silver can give a message a meaningful name once its meaning is established with evidence.

| Table | One row is | Why it is kept |
|---|---|---|
| `session` | One `session` message | Activity summary |
| `lap` | One `lap` message | Grain between session and record |
| `record` | One `record` message | Activity time series |
| `activity` | One `activity` message | Activity-level metadata |
| `monitoring` | One `monitoring` message | Background monitoring time series |
| `stress_level` | One `stress_level` message | Stress time series |
| `unknown_*` | One message of that `unknown_*` type, one table per type | Supporting data from file types 49, 68 and 44; meaning not established. Type 49 contains `unknown_273`, `unknown_346`, `unknown_275` and `unknown_382`. |
| `file_id` | One `file_id` message, so one per file | File-level metadata: creation time, device serial number, raw file type |
| `device_info` | One `device_info` message | Device, sensor and firmware provenance. A change in device or sensor can explain a shift in the data that is not a change in the athlete. |
| `timestamp_correlation` | One `timestamp_correlation` message | Raw material for the timestamp and timezone strategy. Needed as evidence before the time model is decided. |

Bronze loads only the message types in this table, even when a retained file contains others. The scope rule applies at every level: file types, message types and fields.

**Open:** the `unknown_*` message names in file types 68 and 44 are not yet listed. Until they are, no messages from those file types are loaded.

## JSON tables

Each JSON table holds one kind of record. A row is one element of the file's array of records, and everything nested inside that element stays in the same row: nested objects become struct columns and nested arrays become array columns. Flattening them is a Silver task.

| Table | Source family | One row is |
|---|---|---|
| `daily_wellness` | `daily_wellness` | One day's wellness report |
| `sleep` | `sleep` | One sleep record |
| `vo2_max` | `performance`, Activity VO2 Max | One recorded VO2 Max value |
| `max_met` | `performance`, Max MET | One recorded Max MET value |
| `fitness_age` | `performance`, fitness age | One recorded fitness-age value |
| `summarized_activities` | `summarizedActivities` | One activity |

- **Why `performance` is three tables:** it contains three record structures with different fields. One table would mix rows that mean different things, which is the same problem that led to one table per message type for FIT.
- **Hydration:** the nested `hydration` object in `daily_wellness` is not loaded, because hydration is out of scope. This removes a field. It does not change any value that is kept.
- **Performance rows:** a new record most likely appears each time Garmin recalculates the metric, for example after a workout. This is an inference, not verified. Max MET has several records on some dates, and VO2 Max records carry an `activityId`.
- **`summarizedActivities`:** the records are not at the top level of the file but in the array under the key `summarizedActivitiesExport`.
- **Data observations for Silver:** some sleep records have no `calendarDate`, and some Max MET dates have more than one record. Bronze keeps these as they are.

### JSON lineage columns

| Column | Holds | Why it is needed |
|---|---|---|
| `_source_path` | The relative path of the JSON file inside the export. | Same as for FIT. |
| `_record_index` | The position of the record in the file's array of records: 0 for the first, and so on. | JSON records have no guaranteed natural key: some have no date, and some dates repeat. Together with `_export_sha256` and `_source_path`, it identifies exactly one row. |
| `_loaded_at` | When the pipeline loaded the row, as a timestamp. | Same as for FIT. |
| `_export_sha256` | The SHA-256 hash of the uploaded export ZIP. | Same as for FIT. |

JSON tables have no `_file_type` column, because each table holds a single family and the table name already says which one.

## Lineage columns

Every FIT table gets these columns, added by the pipeline. The lineage columns for JSON tables are decided in the JSON section. They are not part of the Garmin data. Their names start with `_` so they can never clash with a Garmin field name, and so it is clear which columns the pipeline added.

| Column | Holds | Why it is needed |
|---|---|---|
| `_source_path` | The relative path of the FIT file the message came from, inside the export. | Traces a row directly to its file, and stays unique even if two files in different folders share a name. |
| `_file_type` | The FIT file type of that file. | The same message type can come from more than one file type, and this column tells them apart. |
| `_message_index` | The position of the message in its file: 0 for the first message, 1 for the next, and so on. | `timestamp_16` reconstruction depends on message order. It is also part of the row key. |
| `_loaded_at` | When the pipeline loaded the row, as a timestamp. | Identifies the pipeline run. A timestamp rather than a date keeps two runs on the same day apart. |
| `_export_sha256` | The SHA-256 hash of the uploaded export ZIP. | Identifies the export. Load time cannot do this, because loading the same ZIP twice gives two different load times, while the hash stays the same. |

### Row key

`_export_sha256` + `_source_path` + `_message_index` identifies exactly one row. All three are needed: every file has a message at index 0, and the same file can appear in more than one export.

### Loading the same export twice

Before loading, the pipeline checks whether the export's `_export_sha256` is already in Bronze. If it is, the export is skipped. Reloading an identical ZIP adds no information, and skipping it keeps the row key unique. Running the pipeline twice on the same input therefore changes nothing (the load is idempotent).

### Loading a newer export

A newer export does not replace an older one: all exports are kept. A newer Garmin export is not guaranteed to contain everything an older one did. Part of an export can be missing, as happened with an earlier export of this dataset. An activity deleted in Garmin Connect would also be expected to be missing from later exports, although this has not been tested. Deleting an older export could therefore lose data permanently, while keeping it costs only disk space.

Successive exports overlap, so the same data can appear more than once in Bronze. Removing duplicates across exports is a Silver task.
