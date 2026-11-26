# Garmin Data Reconnaissance

**Checkpoint:** 3 November 2026, updated 23 November 2026 with the numeric-type and linkage findings  
**Purpose:** Record the understanding of the source data before ingestion and data-model work.

All figures describe the current Garmin export, requested in November 2026. It replaced an earlier export that was missing one archive (see section 13).

## 1. Source inventory

The preserved Garmin export is the source of truth.

| Source | Count | Current role |
|---|---:|---|
| FIT files | 25,148 | Primary raw source |
| JSON files | 172 | Supporting/longitudinal source |
| GPX files | 7 | Inventoried; no current analytical role established |
| PNG files | 3 | Inventoried; no current analytical role established |
| TXT files | 1 | Inventoried; no current analytical role established |
| BAK files | 1 | Inventoried; no current analytical role established |

The raw export contains nested ZIP archives. The master ZIP was re-zipped on macOS, so it also contains metadata files, which extraction skips. The ZIP remains untouched.

## 2. FIT classification

| FIT type | Count | Decision |
|---|---:|---|
| `monitoring_b` | 7,912 | KEEP |
| `activity` | 740 | KEEP |
| `44` | 7,263 | DROP (November 2026, see section 6) |
| `49` | 1,106 | KEEP: sleep |
| `68` | 1,019 | KEEP: heart-rate variability |
| `58` | 5,708 | DROP for current scope |
| `41` | 651 | DROP for current scope |
| `79` | 521 | DROP for current scope |
| `57` | 225 | DROP for current scope |
| `72` | 1 | DROP for current scope |
| `74` | 1 | DROP for current scope |
| `segment_list` | 1 | DROP for current scope |
| **Total** | **25,148** | |

The numeric FIT identifiers are not treated as semantic names. The retained/supporting decisions are scope decisions based on observed structure, not claims that excluded types are universally useless.

### Retained profile

The retained profile covers **18,040 FIT files**, the retained scope at the time, which included type `44`. The profile was generated after filtering by `file_id.type`; the 7,108 excluded FIT files were not fully profiled. With type `44` removed, the retained scope is **10,777 FIT files**.

The profile was produced with the `fitparse` library, whose FIT profile is older than Garmin's current one: it knows no message above number 268, and also lacks 13, 104, 211, 216 and 229. It reports messages it does not know as `unknown_<number>`. Section 6 adds the official names from Garmin's FIT profile (version 21.221.0) where they exist.

## 3. Activity structure

The core activity hierarchy is:

```text
activity
├── session
├── lap
└── record
```

Observed retained profile:

- `session`: 740 messages across 740 activity files, with one session per file.
- `lap`: 3,942 messages across 680 activity files.
- `record`: 2,682,496 messages across all 740 activity files.
- `activity`: 740 activity-level messages.

The `record` grain is the primary activity time-series source. Fields include timestamps, heart rate, distance, speed, cadence, power, temperature, altitude and encoded position fields, with strong activity-dependent sparsity.

## 4. Monitoring structure

`monitoring_b` contains:

- 7,912 files
- 1,717,174 `monitoring` messages

Important observed fields include timestamp, activity type, heart rate, steps, distance, active time/calories and intensity-related measurements.

Monitoring is a separate longitudinal grain and must not be directly flattened into activity records.

## 5. Stress

The retained profile contains:

- 6,327 files
- 1,458,399 `stress_level` messages

`stress_level_value` ranges from -2 to 100. Negative values, including `-1` and `-2`, must be treated as special/unavailable values rather than ordinary stress scores. The working interpretation is in `docs/data_dictionary.md`, section 3.

## 6. Numeric FIT types

Types `44`, `49` and `68` are not defined in Garmin's official FIT profile. In November 2026 their messages were compared with the profile's message definitions, across all files of each type.

### Type `49`: sleep

Night files (1,025) contain `sleep_level` (`fitparse`: `unknown_275`) and `sleep_assessment` (`unknown_346`), both defined in the official profile, plus the undefined `unknown_273` and `unknown_382`. Nap files (81) contain only `nap_event` (`unknown_412`). Every type-49 file is one of the two kinds. Details are in `docs/data_dictionary.md`, section 3.

### Type `68`: heart-rate variability

All 1,019 files contain `hrv_status_summary` (`unknown_370`) and `timestamp_correlation`; 1,003 contain `hrv_value` (`unknown_371`), the official "5 minute RMSSD". The undefined `unknown_22` is also in every file.

### Type `44`: dropped

Of 20 message types, only `max_met_data` (`unknown_229`) is defined in the official profile, and it most likely duplicates the retained JSON Max MET data. The type was removed from the scope.

Messages the official profile does not define are not assigned a meaning.

## 7. JSON inventory

The 172 JSON files were grouped into:

| Family | Files | Decision |
|---|---:|---|
| `daily_wellness` | 13 | KEEP |
| `sleep` | 11 | KEEP |
| `performance` | 15 | SUPPORTING |
| `hydration` | 13 | DROP |
| `health_status` | 5 | DROP |
| `environmental` | 11 | DROP |
| `garmin_derived` | 59 | DROP |
| `low_level` | 45 | DROP, except the 3 `summarizedActivities` files (KEEP) |

The retained JSON scope is therefore **42 files**.

`summarizedActivities`, part of `low_level`, is the only source found that lists every activity. It was added to the retained scope in November 2026, during the Bronze design, because the link between JSON and FIT activities depends on it.

### Daily wellness

1,106 records were profiled. The useful grain is daily, with heart-rate summaries, activity duration, steps, distance, calories, stress, Body Battery and respiration.

Nested hydration data is explicitly excluded and is not profiled. Garmin-estimated hydration/sweat-loss values are not suitable as independent ground truth for this thesis.

### Sleep

1,003 records across 11 files, covering 989 distinct calendar dates.

Observed data includes sleep start/end, deep/light/REM/awake durations, respiration, sleep stress, sleep scores, awakenings, restlessness and naps.

### Performance

15 files containing VO2 Max, Max MET and fitness-age-related Garmin-derived observations.

These remain supporting observations, not independent ground truth.

## 8. Temporal findings

The retained profile contains multiple temporal representations:

- FIT timestamps
- FIT local timestamps
- FIT `start_time`
- FIT `time_created`
- FIT timestamp-correlation fields
- JSON GMT timestamps
- JSON calendar dates/local timestamps

Observed date ranges differ by source:

| Source field | Earliest | Latest |
|---|---|---|
| FIT `record.timestamp` | 2023-05-25 | 2026-11-01 |
| FIT `monitoring.timestamp` | 2024-01-08 | 2026-11-02 |
| JSON `daily_wellness` | 2023-05-24 | 2026-11-02 |
| JSON `sleep` | 2024-01-08 | 2026-11-02 |
| JSON `performance` | 2024-01-31 | 2026-11-02 |

Three FIT fields fall outside the main analytical range and must not be used to describe its span:

- `device_info.timestamp` has a minimum of 2015-01-06.
- `training_file.time_created` has a minimum of 2022-12-23.
- `activity.local_timestamp` ranges from 1989-12-31 to 2046-10-31. The minimum comes from 38 activities where the field is 0, the FIT epoch, meaning not set. The maximum comes from 11 activities whose value differs from `timestamp` by more than any timezone allows. The other 691 give a valid timezone offset. Details are in `docs/data_dictionary.md`, section 7.

This is a modeling problem to solve explicitly, not a reason to guess a canonical timezone. The ingestion layer must define timestamp and date semantics.

## 9. Missingness and sparsity

Missingness is frequently structural:

- power is activity-dependent;
- cadence is activity-dependent;
- running biomechanics are sparse;
- distance/speed vary by activity;
- some session fields are not applicable to all sports.

Therefore:

> missing does not automatically mean invalid.

The quality layer must distinguish not-applicable, unavailable, explicit null, malformed and unexpected missingness.

Both `monitoring.heart_rate` and `record.heart_rate` have a minimum of 0. The working interpretation is a missed reading, which Silver treats as missing (`docs/data_dictionary.md`, section 3).

## 10. Relationships and identifiers

Candidate identifiers are:

- FIT source filename
- FIT `file_id.number`
- FIT `file_id.serial_number`
- activity timestamps/start time
- JSON `activityId`
- JSON `activityUuid.uuid`
- JSON `userProfilePK`
- JSON `deviceId`
- JSON `calendarDate`

The number in a FIT filename is not an `activityId`, so filenames cannot link FIT and JSON activities. Start time can (see section 13). Global uniqueness of the remaining identifiers is not yet proven and belongs to ingestion and model validation.

## 11. Conclusion

We now have:

- complete source counts;
- FIT type classification and current scope;
- retained FIT profile;
- activity/session/lap/record structure;
- monitoring structure;
- stress observations;
- JSON family inventory;
- retained JSON scope;
- hydration exclusion;
- sleep/recovery/performance source identification;
- major temporal representations;
- sparsity patterns;
- a verified link between FIT and JSON activities;
- a verified method for monitoring timestamps;
- unresolved-field limitations;
- first data dictionary.

No proprietary `unknown_*` fields have been assigned invented semantics.

## 12. Next steps

```text
raw Garmin export
      ↓
reproducible extraction/parsing
      ↓
identifier + timestamp strategy
      ↓
multi-grain structured model
      ↓
first processed datasets
```

The next milestone is **not more broad reconnaissance**. It is reproducible ingestion and data modeling.

## 13. Export completeness and activity linkage

`src/recon/verify_activity_coverage.py` reproduces the coverage results below.

### Why the export was replaced

The earlier export contained `UploadedFiles` archives Part1 and Part3, with no Part2, and every regular FIT type had a gap of about a year from 14 April 2025. The current export contains all three, and the gap is gone, which confirms that the missing archive was the cause.

| Archive | FIT files |
|---|---:|
| `UploadedFiles` Part1 | 8,494 |
| `UploadedFiles` Part2 | 11,500 |
| `UploadedFiles` Part3 | 5,152 |

Extraction wrote 25,332 files with no name collisions, and none of the archives was corrupt.

Before the earlier export was deleted, it was compared with the current one. No wellness, sleep, health-status or hydration day and no activity was missing from the current export. 14 FIT files of the out-of-scope type `41` were absent, for reasons not investigated, and 30 files had changed. Of those, 3 daily-wellness records differed, and the current values are used.

### Remaining FIT gaps

Gaps of 30 days or more in FIT file creation times:

| FIT type | After | Before | Days | Interpretation |
|---|---|---|---:|---|
| `activity` | 2024-03-20 | 2024-05-05 | 46 | JSON lists no activities either, so most likely no activities were recorded |
| `44` | 2023-09-30 | 2024-01-08 | 100 | Most likely the period before the wearable was in regular use: the gap ends on the day `monitoring_b`, type `49` and type `68` files begin, from the same device product. Type `44` is now out of scope. |
| `57` | 2025-06-07 | 2025-07-11 | 34 | Not established; this type is irregular and out of scope |
| `57` | 2025-11-18 | 2026-02-18 | 91 | As above |
| `57` | 2026-02-18 | 2026-06-03 | 104 | As above |

`monitoring_b`, `49`, `58` and `68` have no such gaps. Monitoring begins on 2024-01-08, so it does not cover the first months of activity data.

### Activity linkage

`summarizedActivities` JSON lists 748 activities, compared with 740 `activity` FIT files. Comparing start times, after converting JSON epoch milliseconds to UTC:

| Result | JSON activities |
|---|---:|
| Exact start-time match to a FIT activity | 739 |
| Start within 5 minutes of a FIT activity | 1 |
| No FIT activity | 8 |
| **Total** | **748** |

All 740 FIT activities therefore link to a JSON activity: 739 exactly, and one with a 13-second difference. That last one is the same activity, on strong evidence: its FIT elapsed time and distance equal the JSON duration and distance exactly, with JSON distance in centimetres and duration in milliseconds. Its FIT sport is `generic`, while its JSON type is `mountain_biking`, so sport labels cannot confirm a link.

**Linking rule:** match exact start times first. Allow a tolerance only for activities still unmatched, and link each FIT file to at most one JSON activity. A tolerance alone is unsafe, because separate activities can start seconds apart.

### Activities without FIT files

- 7 fall in March 2025, all without a manufacturer value. Each starts at exactly the time of the first track point of one of the 7 GPX files, so the GPX files are their source, on strong evidence. GPX is out of scope, so these activities have only their JSON summary.
- 1 falls in July 2026 and is unexplained. It has a device and manufacturer but no FIT or GPX file. It is kept as a known gap: an activity with a summary but no time series.

These activities still have JSON summary values, but no record-level time series in FIT.

## 14. Monitoring timestamp reconstruction

`src/recon/verify_monitoring_timestamps.py` reproduces the results below.

Of 1,717,174 `monitoring` messages, 388,560 have `timestamp` and 1,328,614 have `timestamp_16`.

`timestamp_16` holds the low 16 bits of a FIT timestamp, so it repeats every 65,536 seconds, about 18.2 hours. The full time is the first time at or after the previous known time whose low 16 bits match:

```text
time = previous + ((timestamp_16 - previous) & 0xFFFF)
```

Garmin's forums attribute this formula to the FIT SDK's `MonitoringReader.java`. A Garmin representative has also said the field's use is not explained in their documentation, so the formula rests on those sources and the checks below.

| Check, across 7,912 `monitoring_b` files | Result |
|---|---|
| `timestamp_16` values reconstructed | 1,328,614 of 1,328,614 |
| Values with no earlier full timestamp in the file | 0 |
| Full timestamps earlier than the preceding message's time | 0 of 380,648 |
| Hidden test: full timestamps recomputed from their low 16 bits | 380,642 of 380,648 exact |
| Times more than one day from the file's `time_created` | 0 |

The strongest check is the third: every real timestamp is at or after the time before it, including reconstructed times.

The hidden test only shows whether consecutive times are less than one rollover apart. Its 6 failures are real gaps of 18.4 to 20.9 hours, longer than the 18.2-hour rollover. They do no harm at those points, because those messages carry a full timestamp. They do show that gaps this long occur, so a similar gap between two `timestamp_16` messages would come out about 18.2 hours too early, and could not be detected from the field itself. The one-day check limits how far such an error could go.
