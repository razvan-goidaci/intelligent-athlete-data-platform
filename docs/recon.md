# Garmin Data Reconnaissance

**Checkpoint:** 27 October 2026  
**Purpose:** Freeze the October source-understanding phase before November ingestion and data-model work.

## 1. Source inventory

The preserved Garmin export is the source of truth.

| Source | Count | Current role |
|---|---:|---|
| FIT files | 12,872 | Primary raw source |
| JSON files | 161 | Supporting/longitudinal source |
| PNG files | 3 | Inventoried; no current analytical role established |

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

`stress_level_value` ranges from -2 to 100. `-1` occurs and must be treated as a special/unavailable value rather than an ordinary stress score.

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

The retained profile includes observed timestamps from **2015-01-06** through **2026-10-03**.

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
