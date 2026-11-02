# Garmin Data Reconnaissance

**Checkpoint:** 27 October 2026  
**Purpose:** Freeze the October source-understanding phase before November ingestion and data-model work.

## 1. Source inventory

The preserved Garmin export is the source of truth.

| Source | Count | Current role |
|---|---:|---|
| FIT files | 12,872 | Primary raw source |
| JSON files | 161 | Supporting/longitudinal source |
| GPX files | 7 | Inventoried; no current analytical role established |
| PNG files | 3 | Inventoried; no current analytical role established |
| TXT files | 1 | Inventoried; no current analytical role established |
| BAK files | 1 | Inventoried; no current analytical role established |

The raw export contains nested ZIP archives. The original archive remains untouched.

## 2. FIT classification

| FIT type | Count | Decision |
|---|---:|---|
| `activity` | 433 | KEEP |
| `monitoring_b` | 3,964 | KEEP |
| `44` | 3,590 | SUPPORTING / REVIEW |
| `49` | 659 | SUPPORTING / REVIEW |
| `68` | 598 | SUPPORTING / REVIEW |
| `58` | 3,165 | DROP for current scope |
| `41` | 271 | DROP for current scope |
| `79` | 148 | DROP for current scope |
| `57` | 42 | DROP for current scope |
| `72` | 1 | DROP for current scope |
| `74` | 1 | DROP for current scope |
| **Total** | **12,872** | |

The numeric FIT identifiers are not treated as semantic names. The retained/supporting decisions are scope decisions based on observed structure, not claims that excluded types are universally useless.

### Retained profile

The retained profile covers **9,244 FIT files**. The profile was generated after filtering by `file_id.type`; excluded FIT types were not fully profiled.

## 3. Activity structure

The core activity hierarchy is:

```text
activity
├── session
├── lap
└── record
```

Observed retained profile:

- `session`: 433 messages across 433 activity files.
- `lap`: 2,116 messages across 373 activity files.
- `record`: 1,267,008 messages across all 433 activity files.
- `activity`: 433 activity-level messages.

The `record` grain is the primary activity time-series source. Fields include timestamps, heart rate, distance, speed, cadence, power, temperature, altitude and encoded position fields, with strong activity-dependent sparsity.

## 4. Monitoring structure

`monitoring_b` contains:

- 3,964 files
- 996,693 `monitoring` messages

Important observed fields include timestamp, activity type, heart rate, steps, distance, active time/calories and intensity-related measurements.

Monitoring is a separate longitudinal grain and must not be directly flattened into activity records.

## 5. Stress

The retained profile contains:

- 3,541 files
- 867,987 `stress_level` messages

`stress_level_value` ranges from -2 to 100. Negative values, including `-1` and `-2`, must be treated as special/unavailable values rather than ordinary stress scores. Their exact meanings are not established.

## 6. Supporting FIT sources

### Type `49`

The profile exposes structures such as `unknown_273`, `unknown_346`, `unknown_275` and `unknown_382`. Their semantics are not established.

### Type `68`

Retained as an HRV-related supporting source, but the current profile does not provide enough reliable semantic mapping to freeze a core schema.

### Type `44`

Retained as a supporting metrics source. Its current profile contains substantial unresolved `unknown_*` structure.

No unresolved field is assigned a meaning without evidence.

## 7. JSON inventory

The 161 JSON files were grouped into:

| Family | Files | Decision |
|---|---:|---|
| `daily_wellness` | 13 | KEEP |
| `sleep` | 10 | KEEP |
| `performance` | 14 | SUPPORTING |
| `hydration` | 13 | DROP |
| `health_status` | 4 | DROP |
| `environmental` | 10 | DROP |
| `garmin_derived` | 53 | DROP |
| `low_level` | 44 | DROP |

The retained JSON scope is therefore **37 files**.

### Daily wellness

Approximately 1,074 records were profiled. The useful grain is daily, with heart-rate summaries, activity duration, steps, distance, calories, stress, Body Battery and respiration.

Nested hydration data is explicitly excluded. Garmin-estimated hydration/sweat-loss values are not suitable as independent ground truth for this thesis.

### Sleep

Approximately 971 records across 10 files.

Observed data includes sleep start/end, deep/light/REM/awake durations, respiration, sleep stress, sleep scores, awakenings, restlessness and naps.

### Performance

14 files containing VO2 Max, Max MET and fitness-age-related Garmin-derived observations.

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
| FIT `record.timestamp` | 2023-05-25 | 2026-09-28 |
| FIT `monitoring.timestamp` | 2024-01-08 | 2026-10-03 |
| JSON `daily_wellness` | 2023-05-24 | 2026-10-01 |
| JSON `sleep` | 2024-01-08 | 2026-10-01 |
| JSON `performance` | 2024-01-31 | 2026-10-01 |

Three FIT fields fall outside the main analytical range and must not be used to describe its span:

- `device_info.timestamp` has a minimum of 2015-01-06.
- `training_file.time_created` has a minimum of 2022-12-23.
- `activity.local_timestamp` has a minimum of 1989-12-31, which looks like a FIT epoch placeholder and needs verification.

This is a November modeling problem, not an October reason to guess a canonical timezone. The ingestion layer must explicitly define timestamp and date semantics.

## 9. Missingness and sparsity

Missingness is frequently structural:

- power is activity-dependent;
- cadence is activity-dependent;
- running biomechanics are sparse;
- distance/speed vary by activity;
- some session fields are not applicable to all sports.

Therefore:

> missing does not automatically mean invalid.

The December quality layer must distinguish not-applicable, unavailable, explicit null, malformed and unexpected missingness.

## 10. Relationships and identifiers

Candidate identifiers are now known:

- FIT source filename
- FIT `file_id.number`
- FIT `file_id.serial_number`
- activity timestamps/start time
- JSON `activityId`
- JSON `activityUuid.uuid`
- JSON `userProfilePK`
- JSON `deviceId`
- JSON `calendarDate`

Global uniqueness and cross-source relationships are **not yet proven** and belong to November ingestion/model validation.

## 11. October conclusion

The October objective was to understand the source data before designing the pipeline.

That objective is complete.

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
- candidate identifiers;
- unresolved-field limitations;
- first data dictionary.

No final anomaly-detection problem has been forced. No proprietary `unknown_*` fields have been assigned invented semantics.

## 12. November handoff

November starts from the following concrete problem:

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

## 13. Addendum: pre-ingestion checks (1 November 2026)

These read-only checks answer or sharpen questions for November. They do not change the retained scope.

- **Extraction is complete.** The master ZIP contains 13,045 files once nested archives are expanded, and 13,045 are on disk. No filenames collide, so the flat output folders lost nothing.
- **FIT filename numbers are not activity IDs.** No `activityId` equals the number in a FIT filename, so the filename cannot link the two sources.
- **Most monitoring messages have no full timestamp.** Of 996,693 `monitoring` messages, 223,341 have `timestamp` and 773,352 have `timestamp_16`. Ingestion must reconstruct the full time for the latter (see section 15).
- **Monitoring heart rate includes 0.** `monitoring.heart_rate` has a minimum of 0, which needs a decision on whether it means no reading.

## 14. Addendum: FIT coverage gap (2 November 2026)

`src/verify_activity_coverage.py` reproduces the results below.

### Activity linkage

`summarizedActivities` JSON, currently in the dropped `low_level` family, lists 724 activities, compared with 433 `activity` FIT files. Comparing start times, after converting JSON epoch milliseconds to UTC:

| Result | JSON activities |
|---|---:|
| Exact start-time match to a FIT activity | 432 |
| Start within 5 minutes of a FIT activity | 2 |
| No FIT activity | 290 |
| **Total** | **724** |

432 of the 433 FIT activities match exactly, and the remaining one is within 5 minutes of a JSON activity. Start time is therefore a strong link between the two sources. Whether each near match is the same activity has not been checked.

### Missing FIT data

The export's `DI-Connect-Uploaded-Files` folder contains `UploadedFiles` archives **Part1 and Part3, with no Part2**.

| FIT type | Last file before gap | First file after gap | Days |
|---|---|---|---:|
| `activity` | 2025-04-14 | 2025-12-09, then 2026-05-06 | 239, then 147 |
| `monitoring_b` | 2025-04-14 | 2026-05-03 | 383 |
| `44` | 2025-04-14 | 2026-05-03 | 383 |
| `49` | 2025-04-14 | 2026-05-05 | 386 |
| `58` | 2025-04-14 | 2026-05-05 | 385 |
| `68` | 2025-04-14 | 2026-05-06 | 386 |

JSON daily wellness, sleep and activity summaries continue through this period.

**Inference:** the missing Part2 most likely held these FIT files. This has not been confirmed against a new export. All FIT counts in this document describe the files present in this export, not the complete history.

### Activities without FIT files

Of the 290 activities with no FIT file:

- 282 fall between April 2025 and May 2026, inside or next to the gap.
- 7 fall in March 2025, all from one device and on days with the 7 GPX files. The GPX files may be their source, but this has not been confirmed.
- 1 falls in July 2026 and is unexplained.

These activities still have JSON summary values such as duration and distance, but no record-level time series in this export.

## 15. Addendum: monitoring timestamp reconstruction (2 November 2026)

`src/verify_monitoring_timestamps.py` reproduces the results below.

`timestamp_16` holds the low 16 bits of a FIT timestamp, so it repeats every 65,536 seconds, about 18.2 hours. The full time is the first time at or after the previous known time whose low 16 bits match:

```text
time = previous + ((timestamp_16 - previous) & 0xFFFF)
```

Garmin's forums attribute this formula to the FIT SDK's `MonitoringReader.java`. A Garmin representative has also said the field's use is not explained in their documentation, so the formula rests on those sources and the checks below.

| Check, across 3,964 `monitoring_b` files | Result |
|---|---|
| `timestamp_16` values reconstructed | 773,352 of 773,352 |
| Values with no earlier full timestamp in the file | 0 |
| Full timestamps earlier than the preceding message's time | 0 of 219,377 |
| Hidden test: full timestamps recomputed from their low 16 bits | 219,377 of 219,377 exact |
| Times more than one day from the file's `time_created` | 0 |

The strongest check is the third: every real timestamp is at or after the reconstructed time before it. The hidden test shows only that consecutive full timestamps are less than one rollover apart. A jump of more than 18.2 hours between two `timestamp_16` messages could not be detected from the field itself, though the one-day check limits how far such an error could go.
