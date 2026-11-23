# Data Dictionary

## 1. Purpose

This document defines the current data dictionary for the retained Garmin source data, based on automated profiling of the November 2026 export.

The reconnaissance and profiling used the `fitparse` library, whose built-in FIT profile only knows message numbers up to 268. Higher-numbered messages appear in its output as `unknown_<number>`. Where Garmin's official FIT profile (version 21.221.0, published in Garmin's `fit-python-sdk` repository) defines such a message, this dictionary gives the official name. The Bronze pipeline parses with Garmin's official SDK instead (see `docs/bronze_design.md`).

The dictionary is intentionally focused on fields that are relevant to the thesis data model, data-quality work, time-series analysis, anomaly detection, and athlete-performance analysis. Garmin/device metadata and unresolved proprietary fields are recorded separately rather than being treated as meaningful analytical variables without evidence.

## 2. Retained source scope

### FIT

| Source | Files | Role |
|---|---:|---|
| `activity` | 740 | Core activity data |
| `monitoring_b` | 7,912 | Longitudinal/background monitoring |
| Type `49` | 1,106 | Sleep: night and nap files (see section 3) |
| Type `68` | 1,019 | Nightly heart-rate variability (see section 3) |

Total retained FIT files: **10,777**.

Excluded FIT files: **14,371**.

Type `44` (7,263 files) was removed from the retained scope in November 2026. Of its 20 message types, only one is defined in Garmin's official profile, `max_met_data`, which most likely duplicates the retained JSON Max MET data. The other 19 have no documented meaning.

### JSON

| Family | Files | Role |
|---|---:|---|
| `daily_wellness` | 13 | Core daily longitudinal data |
| `sleep` | 11 | Core recovery/sleep data |
| `performance` | 15 | Supporting performance data |
| `summarizedActivities` | 3 | List of every activity; JSON side of the start-time link to FIT activities |

Total retained JSON files: **42**.

`summarizedActivities` was added to the retained scope in November 2026, during the Bronze design. It is the only source found that lists every activity, and the link between JSON and FIT activities depends on it.

Hydration is explicitly excluded.

## 3. FIT message dictionary

### `activity`

One message per FIT activity file in the retained activity source.

| Field | Observed type | Observed range / examples | Role |
|---|---|---|---|
| `timestamp` | datetime | Activity timestamp | Core temporal field |
| `local_timestamp` | datetime | Present where available | Timezone/local-time analysis |
| `event` | enum/string | Activity-related events | Supporting |
| `event_type` | enum/string | Event subtype | Supporting |

The `activity` message identifies the activity-level event structure. The main analytical data is represented by `session`, `lap`, and `record`.

### `session`

One session summary per activity.

| Field | Observed type | Observed range | Role |
|---|---|---:|---|
| `timestamp` | datetime | Activity/session timestamp | Core |
| `start_time` | datetime | Activity start | Core |
| `sport` | enum/string | cycling, running, swimming, generic, etc. | Core |
| `sub_sport` | enum/string | road, indoor_cycling, mountain, etc. | Core |
| `total_distance` | float | 0–113,289.35 | Core |
| `total_elapsed_time` | float | 8.932–26,083.726 | Core |
| `total_timer_time` | float | 8.932–26,026.003 | Core |
| `total_calories` | int | 0–2,844 | Core |
| `avg_heart_rate` | int | 74–164 | Core |
| `max_heart_rate` | int | 75–203 | Core |
| `num_laps` | int | 1–51 | Supporting |
| `total_training_effect` | float | 0–5 | Supporting |
| `max_cadence` | int | 0–156 | Activity-dependent |
| `avg_cadence` | int | 0–133 | Activity-dependent |
| `max_power` | int | 0–1,100 | Activity-dependent |
| `avg_power` | int | 0–366 | Activity-dependent |
| `total_ascent` | int | 0–9,804 | Activity-dependent |
| `total_descent` | int | 0–10,672 | Activity-dependent |
| `total_cycles` | int | 0–19,078 | Activity-dependent |
| `total_work` | int | 0–2,454,700 | Activity-dependent |
| `training_stress_score` | float | 0–234 | Supporting |
| `normalized_power` | int | 0–374 | Cycling/power activities |
| `threshold_power` | int | 0–301 | Cycling/power activities |
| `intensity_factor` | float | 0–1.002 | Cycling/power activities |
| `enhanced_avg_speed` | float | 0–11.074 | Activity-dependent |

Fields that are absent or null for large portions of the activity set are not globally applicable and should remain nullable in the processed model.

### `record`

Timestamped activity time-series observations.

**2,682,496** record messages were profiled.

| Field | Observed type | Observed range | Role |
|---|---|---:|---|
| `timestamp` | datetime | Activity time-series timestamp | Primary time key |
| `heart_rate` | int | 0–203 | Core; 0 needs a decision |
| `distance` | float | 0–113,289.35 | Core where available |
| `speed` | float | 0–23.157 | Activity-dependent |
| `enhanced_speed` | float | 0–30.549 | Activity-dependent |
| `cadence` | int | 0–156 | Activity-dependent |
| `fractional_cadence` | float | 0–0.5 | Activity-dependent |
| `power` | int | 0–1,100 | Cycling/power activities |
| `temperature` | int | 10–45 | Supporting |
| `altitude` | float | -7–695.8 | Activity-dependent |
| `enhanced_altitude` | float | -7–3,638.2 | Activity-dependent |
| `position_lat` | int | FIT encoded coordinate | Spatial |
| `position_long` | int | FIT encoded coordinate | Spatial |
| `resistance` | int | Observed 0 | Activity-dependent |
| `left_right_balance` | int/string | 141–228 observed | Activity-dependent |
| `vertical_oscillation` | float | 33.4–121.8 | Running-dependent |
| `vertical_ratio` | float | 3.99–13.23 | Running-dependent |

`position_lat` and `position_long` are stored in FIT's encoded representation and must be converted during ingestion rather than treated as ordinary decimal coordinates.

`speed`, `cadence`, `power`, altitude, and running-specific fields are sparse because different activities expose different sensor measurements.

### `lap`

Lap-level activity observations.

The profiled source contains lap-level summary fields, including cadence and other activity-dependent measurements. The exact field applicability varies by activity.

The `lap` level should be retained as an intermediate analytical grain between `session` and `record`.

### `monitoring`

Longitudinal monitoring observations from `monitoring_b`.

**1,717,174** monitoring messages were profiled.

| Field | Observed type | Observed range | Role |
|---|---|---:|---|
| `timestamp` | datetime | Full timestamp; present on 388,560 messages | Core |
| `timestamp_16` | int | Truncated time; present on 1,328,614 messages | Core; needs reconstruction |
| `activity_type` | int/string | Garmin activity categories | Core/supporting |
| `active_calories` | int | 0–2,533 | Supporting |
| `active_time` | float | 1–27,879 | Supporting |
| `cycles` | float | 0–11,053 | Supporting |
| `distance` | float | 0–18,688.98 | Supporting |
| `heart_rate` | int | 0–198 | Core; 0 needs a decision |
| `duration_min` | int | 0–1,440 | Supporting |
| `steps` | int | 1–22,106 | Core/supporting |
| `vigorous_activity_minutes` | int | 1–88 | Supporting |
| `moderate_activity_minutes` | int | 1–95 | Supporting |
| `ascent` | float | 0–57.745 | Supporting |
| `descent` | float | 0–43.6 | Supporting |

Monitoring data is a different grain from activity records and must not be merged directly with activity records without an explicit temporal/relational rule.

`heart_rate` has an observed minimum of 0, here and in `record`. It occurs 4,832 times among 1,165,920 monitoring heart-rate values, and 23 times among 2,640,399 record heart-rate values, always mid-activity. Garmin's official profile documents no meaning for 0 in these two messages. It does document 0 as "blank" for the heart-rate field of a related message (`hsa_heart_rate_data`). A heart rate of 0 is not physiologically possible in a living athlete.

**Working interpretation:** 0 is a missed reading. Silver treats it as missing and counts it as a data-quality issue. How missing values are then handled (excluded or filled) is a Silver design decision.

### `stress_level`

Longitudinal stress observations associated with monitoring data.

| Field | Observed type | Observed range | Role |
|---|---|---:|---|
| `stress_level_time` | datetime | Monitoring timestamp | Core temporal field |
| `stress_level_value` | int | -2–100 | Supporting |

Of 1,458,399 stress values, 132,698 are `-1`, 168,045 are `-2` and 2,719 are `0`: about one in five is not a score. Garmin's official profile describes `stress_level_value` as a value "from 1 to 100 calculated by FirstBeat", and documents no meaning for negative values in this message. For a related message (`hsa_stress_data`), it documents `-1` as off wrist and `-2` as excess motion.

**Working interpretation:** `-1`, `-2` and `0` mean no valid stress reading. Silver stores them as a status, not as a score. The `-1` and `-2` meanings are taken by analogy with `hsa_stress_data` and are not confirmed for this message.

Stress is a Garmin-derived score, which Garmin describes as based on heart-rate variability. It is supporting data, not ground truth.

### Type `49`: sleep

Type `49` is not defined in Garmin's official profile, but its contents identify it as sleep data. Every file is one of two kinds:

| Kind | Files | Messages |
|---|---:|---|
| Night | 1,025 | `sleep_level` (fitparse: `unknown_275`), `sleep_assessment` (`unknown_346`), `event`, and the undefined `unknown_273` and `unknown_382` |
| Nap | 81 | `nap_event` (`unknown_412`) |

`unknown_521` appears in 404 files and is not defined in the official profile.

| Message | Official definition |
|---|---|
| `sleep_level` | `timestamp`, `sleep_level` (sleep stage) |
| `sleep_assessment` | Sleep scores 0–100 (overall, quality, duration, recovery, deep, REM, light, awake time, awakenings, restlessness, interruptions), `awakenings_count`, `average_stress_during_sleep` |

The device writes `sleep_assessment` fields 0–16, while the official definition covers fields 0–11, 14 and 15; the extra fields are undocumented.

Files cover 992 distinct days, close to the 989 dated JSON sleep records.

### Type `68`: heart-rate variability

Type `68` is not defined in Garmin's official profile, but its contents identify it as nightly heart-rate variability (HRV) data. All 1,019 files contain:

| Message | Official definition |
|---|---|
| `hrv_status_summary` (fitparse: `unknown_370`) | Weekly average, last-night average, last-night 5-minute high, baseline bands (ms), and an HRV status |
| `hrv_value` (`unknown_371`) | One value per 5 minutes: "5 minute RMSSD", in ms |
| `timestamp_correlation` | UTC, system and local time (see section 4) |

`unknown_22` also appears in every file and is not defined in the official profile.

The device writes `hrv_status_summary` fields 0–8, while the official definition covers fields 0–6; the extra fields are undocumented.

`hrv_value` has 92,056 messages in 1,003 files, about 90 per night. Files cover 989 distinct days. No retained JSON source has an HRV field, so type `68` is the only HRV source in scope.

## 4. FIT metadata

### `file_id`

| Field | Observed information |
|---|---|
| `type` | Identifies the FIT file category |
| `time_created` | File creation timestamp |
| `garmin_product` | Garmin product identifier |
| `manufacturer` | Manufacturer, mainly Garmin; also Zwift |
| `serial_number` | Device serial identifier |
| `number` | File number where present |

`file_id.type` is used for source classification and is not an athlete measurement.

### `device_info`

Contains device and sensor metadata.

Relevant fields include:

- `garmin_product`
- `manufacturer`
- `serial_number`
- `software_version`
- `timestamp`
- `product`
- `device_index`
- `device_type`
- `hardware_version`
- `sensor_position`
- `source_type`
- `descriptor`
- `product_name`

This information is useful for provenance, source differentiation, and debugging but is not part of the primary athlete feature table.

### `timestamp_correlation`

Contains relationships between device/local/system timestamps:

- `local_timestamp`
- `timestamp`
- `system_timestamp`

This is relevant to the timestamp/timezone reconciliation problem and should be investigated before finalizing the temporal data model.

## 5. JSON dictionary

### `daily_wellness`

Daily longitudinal wellness data.

The retained files contain 1,106 records.

| Field | Type | Role |
|---|---|---|
| `calendarDate` | string | Daily grain |
| `userProfilePK` | int | User identifier |
| `uuid` | string | Record identifier |
| `durationInMilliseconds` | int | Record duration |
| `totalKilocalories` | float | Daily energy |
| `activeKilocalories` | float | Active energy |
| `bmrKilocalories` | float | Basal metabolic energy |
| `wellnessKilocalories` | float | Wellness energy |
| `wellnessTotalKilocalories` | float | Daily wellness total |
| `wellnessActiveKilocalories` | float | Active wellness energy |
| `totalDistanceMeters` | int | Daily distance |
| `wellnessDistanceMeters` | int | Wellness distance |
| `totalSteps` | int | Daily steps |
| `dailyStepGoal` | int | Daily step target |
| `highlyActiveSeconds` | int | Highly active duration |
| `activeSeconds` | int | Active duration |
| `moderateIntensityMinutes` | int | Moderate intensity |
| `vigorousIntensityMinutes` | int | Vigorous intensity |
| `isVigorousDay` | bool | Vigorous-day indicator |
| `floorsAscendedInMeters` | float | Elevation gain |
| `floorsDescendedInMeters` | float | Elevation loss |
| `minHeartRate` | int | Daily minimum HR |
| `maxHeartRate` | int | Daily maximum HR |
| `restingHeartRate` | int | Resting HR |
| `currentDayRestingHeartRate` | int | Current-day resting HR |
| `minAvgHeartRate` | int | Minimum average HR |
| `maxAvgHeartRate` | int | Maximum average HR |
| `restingHeartRateTimestamp` | int | Associated timestamp representation |
| `includesWellnessData` | bool | Data availability flag |
| `includesActivityData` | bool | Activity-data availability flag |
| `includesSingleMeasurement` | bool | Measurement availability |
| `includesContinuousMeasurement` | bool | Continuous measurement availability |
| `includesAllDayPulseOx` | bool | All-day pulse-ox availability |
| `includesSleepPulseOx` | bool | Sleep pulse-ox availability |

#### Daily stress

| Field | Type | Role |
|---|---|---|
| `allDayStress.calendarDate` | string | Daily key |
| `allDayStress.aggregatorList[].type` | string | Stress aggregation category |
| `allDayStress.aggregatorList[].averageStressLevel` | int | Average stress |
| `allDayStress.aggregatorList[].maxStressLevel` | int | Maximum stress |
| `allDayStress.aggregatorList[].totalStressCount` | int | Stress observation count |
| `allDayStress.aggregatorList[].stressDuration` | int | Stress duration |
| `allDayStress.aggregatorList[].restDuration` | int | Rest duration |
| `allDayStress.aggregatorList[].activityDuration` | int | Activity duration |
| `allDayStress.aggregatorList[].totalDuration` | int | Total duration |
| `allDayStress.aggregatorList[].lowDuration` | int | Low-stress duration |
| `allDayStress.aggregatorList[].mediumDuration` | int | Medium-stress duration |
| `allDayStress.aggregatorList[].highDuration` | int | High-stress duration |

#### Body Battery

| Field | Type | Role |
|---|---|---|
| `bodyBattery.calendarDate` | string | Daily key |
| `bodyBattery.chargedValue` | int | Daily Body Battery charging |
| `bodyBattery.drainedValue` | int | Daily Body Battery depletion |
| `bodyBattery.bodyBatteryVersion` | float | Garmin version metadata |
| `bodyBattery.bodyBatteryStatList[].bodyBatteryStatType` | string | Stat category |
| `bodyBattery.bodyBatteryStatList[].statsValue` | int | Stat value |
| `bodyBattery.bodyBatteryStatList[].bodyBatteryStatus` | string | Status |
| `bodyBattery.bodyBatteryStatList[].statTimestamp` | string | Timestamp |

Body Battery is Garmin-derived and should be treated as an observed Garmin metric, not as independent ground truth.

#### Respiration

| Field | Type | Role |
|---|---|---|
| `respiration.calendarDate` | string | Daily key |
| `respiration.avgWakingRespirationValue` | float | Average waking respiration |
| `respiration.highestRespirationValue` | float | Maximum respiration |
| `respiration.lowestRespirationValue` | float | Minimum respiration |
| `respiration.latestRespirationValue` | float | Latest respiration |
| `respiration.latestRespirationTimeGMT` | string | Measurement time |

#### Explicitly excluded nested data

The `hydration.*` fields present inside `daily_wellness` are excluded from the thesis model and are not profiled.

This includes:

- `hydration.valueInML`
- `hydration.activityIntakeInML`
- `hydration.goalInML`
- `hydration.sweatLossInML`
- `hydration.adjustedGoalInML`
- related hydration timestamps/flags

These values are not retained because they do not provide suitable independent ground truth for the intended thesis analysis.

### `sleep`

Sleep data contains 1,003 records across eleven exported files, covering 989 distinct calendar dates.

| Field | Type | Role |
|---|---|---|
| `calendarDate` | string | Sleep-day key |
| `sleepStartTimestampGMT` | string | Sleep start |
| `sleepEndTimestampGMT` | string | Sleep end |
| `sleepWindowConfirmationType` | string | Sleep-window classification |
| `deepSleepSeconds` | int | Deep sleep duration |
| `lightSleepSeconds` | int | Light sleep duration |
| `remSleepSeconds` | int | REM duration |
| `awakeSleepSeconds` | int | Awake duration |
| `unmeasurableSeconds` | int | Unmeasurable duration |
| `averageRespiration` | float | Average respiration |
| `lowestRespiration` | float | Minimum respiration |
| `highestRespiration` | float | Maximum respiration |
| `awakeCount` | int | Number of awakenings |
| `avgSleepStress` | float | Average sleep stress |
| `restlessMomentCount` | int | Restless moments |
| `retro` | bool | Retrospective/reprocessed indicator |

#### Sleep scores

| Field | Type | Role |
|---|---|---|
| `sleepScores.overallScore` | int | Overall sleep score |
| `sleepScores.qualityScore` | int | Quality score |
| `sleepScores.durationScore` | int | Duration score |
| `sleepScores.recoveryScore` | int | Recovery score |
| `sleepScores.deepScore` | int | Deep-sleep score |
| `sleepScores.remScore` | int | REM score |
| `sleepScores.lightScore` | int | Light-sleep score |
| `sleepScores.awakeningsCountScore` | int | Awakening score |
| `sleepScores.awakeTimeScore` | int | Awake-time score |
| `sleepScores.restfulnessScore` | int | Restfulness score |
| `sleepScores.interruptionsScore` | int | Interruption score |
| `sleepScores.feedback` | string | Garmin feedback |
| `sleepScores.insight` | string | Garmin insight |

#### Naps

| Field | Type | Role |
|---|---|---|
| `napList[].napTimeSec` | int | Nap duration |
| `napList[].napStartTimestampGMT` | string | Nap start |
| `napList[].napEndTimestampGMT` | string | Nap end |
| `napList[].calendarDate` | string | Associated date |

### `performance`

Performance JSON consists of several related exported datasets.

#### Activity VO2 Max

| Field | Type | Role |
|---|---|---|
| `calendarDate` | string | Date |
| `timestampGmt` | string | Measurement timestamp |
| `sport` | string | Sport |
| `subSport` | string | Sub-sport |
| `activityId` | int | Activity identifier |
| `activityUuid.uuid` | string | Activity UUID |
| `vo2MaxValue` | float | VO2 Max value |
| `deviceId` | int | Device identifier |
| `userProfilePK` | int | User identifier |

#### Max MET / performance metrics

| Field | Type | Role |
|---|---|---|
| `calendarDate` | string | Date |
| `updateTimestamp` | string | Update timestamp |
| `sport` | string | Sport where available |
| `subSport` | string | Sub-sport where available |
| `vo2MaxValue` | float | VO2 Max |
| `maxMet` | float | Maximum MET |
| `maxMetCategory` | string | MET category |
| `calibratedData` | int | Calibration/status indicator |
| `fitnessAge` | string | Garmin fitness-age value where available |

#### Fitness age

The `fitnessAgeData` export contains biometric and derived fields including:

- `asOfDateGmt`
- `chronologicalAge`
- `bmi`
- `rhr`
- `totalVigorousDays`
- `totalVigorousIMs`
- `vo2MaxForHealthyBmiFat`
- `vo2MaxForHealthyActive`
- `biometricVo2Max`
- `currentBioAge`
- `healthyAllBioAge`
- `healthyBmiFatBioAge`
- `healthyActiveBioAge`
- `weightDataLastEntryDate`
- `rhrLastEntryDate`

These are supporting Garmin-derived metrics and should not automatically be treated as independent labels or ground truth.

### `summarizedActivities`

Lists 748 activities, one entry per activity.

| Field | Type | Role |
|---|---|---|
| `activityId` | int | Activity identifier |
| `beginTimestamp` | int | Activity start time, epoch milliseconds (UTC) |

Only these two fields have been verified, by the activity coverage check (`docs/recon.md`, section 13). The family was not part of the retained-data profile, so its other fields have not been profiled yet.

## 6. Identifiers and relationships

The current source contains several candidate identifiers:

| Identifier | Source | Intended use |
|---|---|---|
| FIT file name | FIT | Source-file provenance |
| `file_id.number` | FIT | FIT file identifier where available |
| `file_id.serial_number` | FIT | Device identifier |
| `activityId` | JSON `summarizedActivities`, `performance` | Activity relationship |
| `activityUuid.uuid` | JSON performance | Activity relationship |
| `userProfilePK` | JSON | User identifier |
| `deviceId` | JSON | Device identifier |
| `calendarDate` | JSON | Daily grain |
| `timestamp` / `start_time` | FIT | Time-series/activity relationships |

The final relational model should distinguish:

1. source-file identity;
2. activity identity;
3. timestamp;
4. daily date;
5. device/user provenance.

No assumption should be made that all identifiers are globally unique until checked during ingestion.

The number in a FIT filename is not an `activityId`: none of the 748 `activityId` values in `summarizedActivities` JSON match one.

Start time links FIT and JSON activities: `session.start_time` matches `beginTimestamp`, converted from epoch milliseconds to UTC, exactly for 739 of the 740 FIT activities. The other differs by 13 seconds. The linking rule is in `docs/recon.md`, section 13.

## 7. Temporal model

The data contains several timestamp representations:

- FIT `datetime` values;
- FIT `timestamp`;
- FIT `local_timestamp`;
- FIT `time_created`;
- FIT `start_time`;
- FIT `timestamp_correlation`;
- JSON GMT timestamps;
- JSON local dates/timestamps.

Activity records span **2023-05-25** to **2026-11-01**, and monitoring timestamps span **2024-01-08** to **2026-11-02**.

Earlier values appear only in `device_info.timestamp` (2015-01-06), `training_file.time_created` (2022-12-23) and `activity.local_timestamp`. They do not extend the analytical date range.

`activity.local_timestamp` ranges from 1989-12-31 to 2046-10-31. Both limits are explained by a minority of values:

| `local_timestamp` compared with `timestamp` | Activities |
|---|---:|
| Differs by a whole number of hours within ±14 h (a valid timezone offset) | 691 |
| Equals 0, the FIT epoch (1989-12-31), meaning not set | 38 |
| Differs by more than 14 h (no valid timezone) | 11 |
| **Total** | **740** |

Garmin's official profile defines the field as the timestamp "expressed in local time, used to convert activity timestamps to local time". It is usable as a local-time offset for the 691 activities with a valid offset only. `summarizedActivities` also provides `startTimeLocal`, `startTimeGmt` and `timeZoneId` for every activity.

Monitoring messages that only have `timestamp_16` need their full time reconstructed during ingestion. The method and its checks are in `docs/recon.md`, section 14.

The final model must explicitly define:

- canonical timestamp;
- timezone handling;
- UTC/local conversion;
- activity date;
- sleep date;
- daily wellness date;
- relationship between monitoring and activity timestamps.

## 8. Missingness and sparsity

Missingness is structural rather than necessarily erroneous.

Examples:

- power exists mainly for cycling/power-enabled activities;
- cadence is activity-dependent;
- running-specific biomechanics fields are sparse;
- distance/speed vary by activity type;
- some session metrics are absent for activities where they are not applicable.

Therefore:

**missing ≠ invalid**

The data-quality layer should distinguish:

1. absent because the measurement is not applicable;
2. absent because the sensor/device did not provide it;
3. explicitly null;
4. potentially malformed;
5. genuinely unexpected missingness.

## 9. Unresolved fields

Messages and fields that Garmin's official profile does not define keep their `unknown_*` names and are not assigned invented semantics. They are not loaded into Bronze.

FIT types `49` and `68` were identified in November 2026 from the official message definitions (section 3), and type `44` left the scope.

The remaining unresolved areas are:

1. timestamp/timezone relationships;
2. exact units for fields used in the processed schema;
3. the fields of `summarizedActivities` beyond `activityId` and `beginTimestamp`, to be profiled when Silver selects them.

The FIT-to-JSON activity link is resolved by start time (section 6).

## 10. Current analytical core

The first processed model should prioritize:

### Activity

`activity → session → lap → record`

Core measurements:

- timestamp
- sport/sub-sport
- duration
- distance
- heart rate
- speed
- cadence
- power
- altitude
- temperature
- calories

### Daily wellness

Daily grain:

- calendar date
- heart-rate summaries
- activity duration
- steps
- distance
- calories
- stress
- Body Battery
- respiration

### Sleep

Sleep episode/day:

- start/end
- sleep-stage durations
- respiration
- sleep stress
- sleep scores
- awakenings
- restlessness

### Monitoring

Longitudinal observations:

- timestamp
- heart rate
- activity state
- steps
- distance
- active time/calories
- intensity
- ascent/descent

### Supporting performance

- VO2 Max
- Max MET
- fitness age

## 11. Data-modeling implication

The reconnaissance supports a multi-grain model rather than one large table.

The likely November structure is:

```text
activity
    ├── session
    ├── lap
    └── record

monitoring
    └── monitoring_record

daily_wellness
    ├── daily_stress
    ├── body_battery
    └── respiration

sleep
    ├── sleep_episode
    ├── sleep_scores
    └── naps

performance
    └── performance_observation
```

The final relational/analytical schema should preserve these grains rather than flattening everything into one dataset.

## 12. Current status

Reconnaissance has established:

- retained source scope;
- major FIT message structures;
- activity/session/record hierarchy;
- monitoring structure;
- daily wellness structure;
- sleep structure;
- supporting performance sources;
- major identifiers;
- timestamp types;
- major sparsity patterns;
- explicit exclusions.

The remaining work is primarily semantic resolution and data-model design, not further broad source discovery.
