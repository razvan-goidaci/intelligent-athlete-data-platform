# Data Dictionary

## 1. Purpose

This document defines the current data dictionary for the retained Garmin source data after October reconnaissance and automated profiling.

The dictionary is intentionally focused on fields that are relevant to the thesis data model, data-quality work, time-series analysis, anomaly detection, and athlete-performance analysis. Garmin/device metadata and unresolved proprietary fields are recorded separately rather than being treated as meaningful analytical variables without evidence.

## 2. Retained source scope

### FIT

| Source | Files | Role |
|---|---:|---|
| `activity` | 433 | Core activity data |
| `monitoring_b` | 3,964 | Longitudinal/background monitoring |
| Type `49` | 659 | Supporting source; semantics still partly unresolved |
| Type `68` | 598 | Supporting HRV-related source; semantics still partly unresolved |
| Type `44` | 3,590 | Supporting metrics source; semantics still unresolved |

Total retained FIT files: **9,244**.

Excluded FIT files: **3,628**.

### JSON

| Family | Files | Role |
|---|---:|---|
| `daily_wellness` | 13 | Core daily longitudinal data |
| `sleep` | 10 | Core recovery/sleep data |
| `performance` | 14 | Supporting performance data |

Total retained JSON files: **37**.

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
| `max_heart_rate` | int | 75–189 | Core |
| `num_laps` | int | 1–51 | Supporting |
| `total_training_effect` | float | 0–5 | Supporting |
| `max_cadence` | int | 0–140 | Activity-dependent |
| `avg_cadence` | int | 0–133 | Activity-dependent |
| `max_power` | int | 0–1,078 | Activity-dependent |
| `avg_power` | int | 0–366 | Activity-dependent |
| `total_ascent` | int | 0–9,804 | Activity-dependent |
| `total_descent` | int | 0–10,672 | Activity-dependent |
| `total_cycles` | int | 0–19,078 | Activity-dependent |
| `total_work` | int | 0–2,454,700 | Activity-dependent |
| `training_stress_score` | float | 0–184.3 | Supporting |
| `normalized_power` | int | 0–374 | Cycling/power activities |
| `threshold_power` | int | 0–299 | Cycling/power activities |
| `intensity_factor` | float | 0–0.844 | Cycling/power activities |
| `enhanced_avg_speed` | float | 0–8.659 | Activity-dependent |

Fields that are absent or null for large portions of the activity set are not globally applicable and should remain nullable in the processed model.

### `record`

Timestamped activity time-series observations.

Approximately **1.27 million** record messages were profiled.

| Field | Observed type | Observed range | Role |
|---|---|---:|---|
| `timestamp` | datetime | Activity time-series timestamp | Primary time key |
| `heart_rate` | int | 30–189 | Core |
| `distance` | float | 0–113,289.35 | Core where available |
| `speed` | float | 0–23.157 | Activity-dependent |
| `enhanced_speed` | float | 0–30.549 | Activity-dependent |
| `cadence` | int | 0–140 | Activity-dependent |
| `fractional_cadence` | float | 0–0.5 | Activity-dependent |
| `power` | int | 0–1,078 | Cycling/power activities |
| `temperature` | int | 10–45 | Supporting |
| `altitude` | float | -6.4–695.8 | Activity-dependent |
| `enhanced_altitude` | float | -6.4–3,638.2 | Activity-dependent |
| `position_lat` | int | FIT encoded coordinate | Spatial |
| `position_long` | int | FIT encoded coordinate | Spatial |
| `resistance` | int | Observed 0 | Activity-dependent |
| `left_right_balance` | int/string | 141–228 observed | Activity-dependent |
| `vertical_oscillation` | float | 33.4–119.3 | Running-dependent |
| `vertical_ratio` | float | 4.26–13.23 | Running-dependent |

`position_lat` and `position_long` are stored in FIT's encoded representation and must be converted during ingestion rather than treated as ordinary decimal coordinates.

`speed`, `cadence`, `power`, altitude, and running-specific fields are sparse because different activities expose different sensor measurements.

### `lap`

Lap-level activity observations.

The profiled source contains lap-level summary fields, including cadence and other activity-dependent measurements. The exact field applicability varies by activity.

The `lap` level should be retained as an intermediate analytical grain between `session` and `record`.

### `monitoring`

Longitudinal monitoring observations from `monitoring_b`.

Approximately **996,693** monitoring messages were profiled.

| Field | Observed type | Observed range | Role |
|---|---|---:|---|
| `timestamp` | datetime | Longitudinal monitoring timestamp | Core |
| `activity_type` | int/string | Garmin activity categories | Core/supporting |
| `active_calories` | int | 0–2,456 | Supporting |
| `active_time` | float | 1–27,879 | Supporting |
| `cycles` | float | 0–9,393.5 | Supporting |
| `distance` | float | 0–16,667.79 | Supporting |
| `heart_rate` | int | 0–191 | Core |
| `duration_min` | int | 3–1,440 | Supporting |
| `steps` | int | 3–18,787 | Core/supporting |
| `vigorous_activity_minutes` | int | 1–88 | Supporting |
| `moderate_activity_minutes` | int | 1–61 | Supporting |
| `ascent` | float | 0–57.745 | Supporting |
| `descent` | float | 0.001–43.6 | Supporting |

Monitoring data is a different grain from activity records and must not be merged directly with activity records without an explicit temporal/relational rule.

### `stress_level`

Longitudinal stress observations associated with monitoring data.

| Field | Observed type | Observed range | Role |
|---|---|---:|---|
| `stress_level_time` | datetime | Monitoring timestamp | Core temporal field |
| `stress_level_value` | int | -2–100 | Supporting |

The value `-1` occurs and should be treated as a special/missing/unavailable state rather than an ordinary stress score.

### Type `49`

The source contains several message structures with fields currently exposed by `fitparse` as `unknown_*`.

Observed structures include `unknown_273`, `unknown_346`, `unknown_275`, and `unknown_382`.

The automated profile shows that several fields contain stable numeric values, including fields in `unknown_346` ranging approximately from 0–100.

**Semantic interpretation is not yet frozen.** These fields must not receive invented names or meanings in the processed model.

### Type `68`

The type was retained as a supporting HRV-related source.

The current automated profile exposes proprietary/unknown fields rather than sufficiently reliable semantic names.

**Semantic interpretation is not yet frozen.** The source is retained because it may provide useful recovery/HRV information, but it is not yet part of the core analytical schema.

### Type `44`

The type was retained as supporting metrics data.

Its current profile is dominated by unresolved `unknown_*` fields.

**Semantic interpretation is not yet frozen.** It should not be promoted into the core model until its fields are mapped with sufficient evidence.

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

The retained files contain approximately 1,074 records.

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

The `hydration.*` fields present inside `daily_wellness` are excluded from the thesis model.

This includes:

- `hydration.valueInML`
- `hydration.activityIntakeInML`
- `hydration.goalInML`
- `hydration.sweatLossInML`
- `hydration.adjustedGoalInML`
- related hydration timestamps/flags

These values are not retained because they do not provide suitable independent ground truth for the intended thesis analysis.

### `sleep`

Sleep data contains approximately 971 records across ten exported files.

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

## 6. Identifiers and relationships

The current source contains several candidate identifiers:

| Identifier | Source | Intended use |
|---|---|---|
| FIT file name | FIT | Source-file provenance |
| `file_id.number` | FIT | FIT file identifier where available |
| `file_id.serial_number` | FIT | Device identifier |
| `activityId` | JSON performance | Activity relationship |
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

The FIT profile spans timestamps from **2015-01-06** to **2026-10-03** at the retained-source level.

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

Fields named `unknown_*` are retained in the reconnaissance output but are not assigned invented semantics.

The highest-priority unresolved areas are:

1. FIT type `49`;
2. FIT type `68` / HRV-related data;
3. FIT type `44`;
4. timestamp/timezone relationships;
5. exact units for fields used in the processed schema;
6. identifier relationships between FIT and JSON data.

These are the remaining items that matter for November data modeling.

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

The October reconnaissance has established:

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
