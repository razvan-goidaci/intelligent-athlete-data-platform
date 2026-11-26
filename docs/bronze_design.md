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
- **FIT files:** extraction writes every FIT file in the export to `data/raw/fit`, including excluded file types. The Bronze load reads each file's type from its `file_id` message and loads only the retained types: `activity`, `monitoring_b`, 49 (sleep) and 68 (HRV). A file of any other type produces no rows. Its messages are not loaded either, even when they belong to a table Bronze keeps, such as `file_id` or `device_info`.

## Decision: FIT parser

Bronze parses FIT files with Garmin's official Python SDK, `garmin-fit-sdk`, rather than `fitparse`.

- **Problem:** `fitparse` 1.2.0 knows no message number above 268, and also lacks a few lower ones (13, 104, 211, 216, 229). Garmin's official FIT profile documents many of these that appear in this export, such as `sleep_assessment` (346), `hrv_value` (371) and `respiration_rate` (297). `fitparse` reports them as `unknown_*`, without field names, units or scaling.
- **Options:** keep `fitparse`; keep `fitparse` and maintain a mapping to official names by hand; or use `garmin-fit-sdk`.
- **Decision:** `garmin-fit-sdk`. It provides the official names, units and scaling directly from Garmin's profile, and the Bronze code is not written yet, so switching costs nothing extra.
- **Not changed:** the existing verification scripts keep using `fitparse`. Their results are already recorded in `docs/recon.md`.
- **Cross-check (done, 25 November 2026):** `src/recon/check_sdk_message_counts.py` decodes every FIT file with `garmin-fit-sdk` 21.221.0, using the decoder options below, and counts messages per type in the 10,777 retained files. Every count matches `fitparse`: the core counts in `docs/recon.md` (`record` 2,682,496, `session` 740, `lap` 3,942, `monitoring` 1,717,174, `stress_level` 1,458,399, `activity` 740), and every other message type, including those `fitparse` reports as `unknown_*` (for example `hrv_value` 92,056, `sleep_level` 21,190, `respiration_rate` 1,466,586). The two parsers find the same messages; the SDK adds the official names.
- **Limit of the cross-check:** equal counts do not show equal values. Some values differ by design: for messages `fitparse` does not know, it returns raw integers, while the SDK applies the profile's scale and offset. Values are checked by the Bronze verification step instead.
- **Requirement for the Bronze load:** the count check did not inspect the decoder's `errors`. The Bronze load must record decode errors per file, as a data-quality signal.

### Decoder options

The rule for each option: after it is applied, can we still tell exactly what the device wrote? If yes, it is decoding and stays on in Bronze. If no, it is a transformation and belongs in Silver, where it is a documented decision.

| Option | Bronze | Reason |
|---|---|---|
| `apply_scale_and_offset` | on | Decoding: applies the scale and offset from Garmin's profile. |
| `convert_datetimes_to_dates` | on | Decoding: FIT seconds become datetimes. |
| `convert_types_to_strings` | on | Decoding: enum numbers become their profile names. |
| `expand_sub_fields` | on | Decoding: adds the documented meaning of a field whose meaning depends on another field. The SDK's source adds the sub-field as a new field and keeps the original. |
| `expand_components` | off | Creates new fields, some of them accumulated from earlier messages in the file, which is a calculation across rows. |
| `merge_heart_rates` | off | Copies heart rates from `hr` messages into `record` rows the device did not write them to. Afterwards, original and copied values cannot be told apart. |

The option names were confirmed against `garmin-fit-sdk` 21.221.0, the pinned version, which matches the profile version cited in `docs/data_dictionary.md`.

### Enum values are stored as text

- **Problem:** many FIT fields are enums: the device writes a code number, and the profile gives each code a name, for example `sleep_level` 3 is `deep`. `convert_types_to_strings` replaces a code with its name only when the profile defines that code, and leaves any other code as a number. The same column then holds text in some rows and numbers in others. A sample load of every 50th FIT file found this in 6 of 336 fields (for example `event.event` and `device_info.battery_status`). When all rows are in one DataFrame, Spark silently stores such a column as text. When the load writes in batches, a batch with only numbers would make the column numeric, and a later batch with text would fail.
- **Decision:** for every field whose profile type is an enum, a value the SDK left as a number is stored as text, so 38 becomes `"38"`. The column then always holds text. A purely numeric value means a code the profile does not name.
- **Why this is decoding, not transforming:** the stored text is exactly the code the device wrote.
- **Which fields count as enums:** a field counts as an enum when its profile type is listed in the profile's types. Five listed types are excluded, because they are numbers with only one or two named special values: `date_time`, `local_date_time`, `message_index`, `left_right_balance` and `left_right_balance_100`. Their values stay numbers. Sub-fields such as `garmin_product` are checked by their own type.
- **Result:** after the change, the same sample has no field with mixed types. The full load is checked again in Bronze verification.

## FIT tables

Each table is named after the message's name in the official FIT profile. A message the profile does not define is named `unknown_<number>`, after its message number. Bronze does not give undefined messages a meaningful name, because that would be an interpretation. Silver can name them once their meaning is established with evidence.

| Table | One row is | Why it is kept |
|---|---|---|
| `session` | One `session` message | Activity summary |
| `lap` | One `lap` message | Grain between session and record |
| `record` | One `record` message | Activity time series |
| `activity` | One `activity` message | Activity-level metadata |
| `event` | One `event` message | Start, stop and pause markers. Needed to tell a pause in an activity apart from missing data. |
| `monitoring` | One `monitoring` message | Background monitoring time series |
| `stress_level` | One `stress_level` message | Stress time series |
| `respiration_rate` | One `respiration_rate` message | All-day breathing-rate time series |
| `sleep_level` | One `sleep_level` message | Sleep-stage timeline through the night. JSON sleep has only the stage totals. |
| `sleep_assessment` | One `sleep_assessment` message | Sleep scores. Also in JSON sleep; the two sources can be checked against each other. |
| `hrv_value` | One `hrv_value` message | Heart-rate variability every 5 minutes during the night. The only HRV source in scope. |
| `hrv_status_summary` | One `hrv_status_summary` message | Nightly HRV summary and baseline |
| `file_id` | One `file_id` message, so one per file | File-level metadata: creation time, device serial number, raw file type |
| `device_info` | One `device_info` message | Device, sensor and firmware provenance. A change in device or sensor can explain a shift in the data that is not a change in the athlete. |
| `timestamp_correlation` | One `timestamp_correlation` message | Raw material for the timestamp and timezone strategy. Needed as evidence before the time model is decided. |

Bronze loads only the message types in this table, even when a retained file contains others. The scope rule applies at every level: file types, message types and fields.

The same applies to fields: a field the official profile does not define is not loaded, even inside a defined message. For example, `record` messages in this export carry several such fields, which the SDK reports by field number instead of a name. Undefined fields beyond a message's official definition, such as the extra fields in `sleep_assessment` and `hrv_status_summary`, are dropped the same way.

Developer fields are not loaded either. A third-party app can add its own fields to Garmin's messages, and the SDK collects them in a nested dictionary under the key `developer_fields`. Only the app describes these fields, inside the file. Garmin's profile does not define them, so they fall under the same rule. They occur in 15 activity files.

Messages the official profile does not define are not loaded, so Bronze has no `unknown_*` tables. Their meaning cannot be established from any official source, and none is needed by the coach. If that changes, they can be ingested again from the export ZIP.

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
- **Performance rows:** every VO2 Max record carries an `activityId` that exists in `summarizedActivities`, so a VO2 Max row is most likely one value computed from one activity. Max MET records come in two categories, `CYCLING` and `GENERIC`, and most repeated dates hold one record of each. Fitness age has one record per date. These are inferences from the record structure, not documented by Garmin.
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
| `_file_type` | The FIT file type of that file, as text: `activity`, `monitoring_b`, `49` or `68`. | The same message type can come from more than one file type, and this column tells them apart. It is always text so it has the same type in every table, including for the two numeric types. |
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
