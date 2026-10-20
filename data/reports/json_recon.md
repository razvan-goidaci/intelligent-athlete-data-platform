# Garmin JSON Data-Family Reconnaissance

## Purpose

Classify the Garmin JSON export at the **data-family/category level**, not file-by-file.

The individual JSON files are mostly time-sliced exports of the same underlying data families. The goal is to decide which **families of data** are relevant to the thesis pipeline.

This is reconnaissance, not final data modeling.

---

## Decision Categories

### KEEP

Raw or sufficiently close-to-raw measurements likely to become part of the thesis data pipeline.

### SUPPORTING

Useful context, comparison, validation, or reference data, but not a primary source.

### DROP

Not relevant to the current thesis scope, or redundant/unhelpful.

> **Important:** Garmin-derived scores/statuses should **not automatically be treated as ground truth** for the anomaly-detection model.

---

# 1. Daily Wellness

**Category:** `daily_wellness`  
**File family:** `UDSFile_*`  
**Exported files:** 13

## What this family contains

Daily wellness measurements. Observed fields include examples such as:

- calendar date
- total / active calories
- distance
- steps
- resting heart rate
- minimum / maximum heart rate
- stress
- Body Battery
- respiration
- hydration
- activity-related durations
- other daily wellness measurements

## What to determine

- Does this provide useful raw daily measurements beyond FIT?
- Which fields are genuinely useful for the thesis?
- Which fields overlap with other sources?
- Are schema changes over time significant?

## Decision

- [X] KEEP
- [ ] SUPPORTING
- [ ] DROP

## Rationale

Contains important daily body and activity measurements such as resting heart rate, steps, active calories, and total calories, which can serve as important building blocks for our analysis.

The data is sufficiently close to the primary measurements captured by the device to make this family valuable for the thesis. Some fields may still involve Garmin processing, so individual measurements should be evaluated before being treated as raw ground truth.

---

# 2. Sleep

**Category:** `sleep`  
**File family:** `*_sleepData.json`  
**Exported files:** 10

## What this family contains

Sleep observations including:

- sleep start/end
- calendar date
- total sleep duration
- deep / light / REM sleep
- awake time
- unmeasurable time
- respiration
- sleep stress
- awakenings / restless moments
- sleep scores

## What to determine

- Does this provide useful recovery information?
- Which measurements could become anomaly-detection features?
- How can sleep observations be aligned with activities/daily wellness?

## Decision

- [X] KEEP
- [ ] SUPPORTING
- [ ] DROP

## Rationale

Contains important sleep and recovery measurements that may be useful for the analysis.

The main sleep measurements can potentially be used as features when analysing relationships between recovery, training, and anomalies. Garmin-generated sleep scores and conclusions will not be treated as ground truth; the focus will remain on the underlying measurements.

---

# 3. Hydration

**Category:** `hydration`  
**File family:** `HydrationLogFile_*`  
**Exported files:** 13

## What this family contains

Hydration events and measurements including:

- amount in milliliters
- hydration source
- activity ID
- timestamps
- estimated sweat loss
- duration
- UUID

## What to determine

- Is hydration sufficiently complete/reliable to be useful?
- Does it contribute meaningful information to athlete training/recovery analysis?
- Is it useful for anomaly detection or mainly contextual?

## Decision

- [ ] KEEP
- [X] SUPPORTING
- [ ] DROP

## Rationale

The hydration data appears limited because it does not provide sufficiently complete information about actual fluid intake.

Estimated sweat loss may provide some contextual information, but it is itself an estimate and therefore should not be treated as a highly reliable measurement.

For this reason, hydration is better treated as supporting information rather than a core part of the analytical pipeline.

---

# 4. Health Status

**Category:** `health_status`  
**File family:** `*_healthStatusData.json`  
**Exported files:** 4

## What this family contains

Health-status observations with:

- calendar date
- creation/update timestamps
- outlier count
- `metrics`

## What to determine

- What is actually contained inside `metrics`?
- Is it raw measurement data or Garmin-derived assessment data?
- Does it provide information not already available elsewhere?

## Decision

- [ ] KEEP
- [ ] SUPPORTING
- [X] DROP

## Rationale

This family appears to contain Garmin-derived health-status information rather than measurements that are necessary for our own analysis.

Since the thesis is focused on analysing the underlying data and developing our own data-quality and anomaly-detection approach, Garmin-derived conclusions are not required when the underlying measurements are available from other data families.

---

# 5. Performance

**Category:** `performance`  
**File families:** `ActivityVo2Max_*`, `MetricsMaxMetData_*`, `fitnessAgeData`  
**Exported files:** 14

## What this family contains

Performance-related measurements such as:

- VO₂ max
- sport / sub-sport
- activity ID / UUID
- timestamps
- maximum MET
- fitness-age-related measurements
- physiological performance measurements

## What to determine

- Which measurements are sufficiently close to raw observations?
- Which are useful performance outcomes/features?
- Which are Garmin-derived estimates that should only be supporting data?

## Decision

- [ ] KEEP
- [X] SUPPORTING
- [ ] DROP

## Rationale

Measurements such as VO₂ max may be useful for long-term trend analysis and as contextual performance indicators.

However, many of these values are Garmin-derived estimates rather than direct measurements. They may therefore be useful as supporting information, but they should not be treated as equivalent to raw sensor data or as ground truth for the anomaly-detection model.

---

# 6. Environmental

**Category:** `environmental`  
**File family:** `MetricsHeatAltitudeAcclimation_*`  
**Exported files:** 10

## What this family contains

Environmental/acclimation-related observations, including altitude/heat-related measurements and timestamps.

## What to determine

- Does environmental context materially improve interpretation of training/performance anomalies?
- Is the information useful enough to carry through the pipeline?
- Does its coverage justify keeping it?

## Decision

- [ ] KEEP
- [ ] SUPPORTING
- [X] DROP

## Rationale

The environmental/acclimation data is not sufficiently important for the current scope of the bachelor's thesis.

In particular, altitude and heat acclimation would become more relevant in a more specialised analysis involving environmental training conditions or altitude-camp training. This is outside the current thesis focus, so the category can be excluded from the main pipeline.

---

# 7. Garmin-Derived

**Category:** `garmin_derived`  
**File families:**

- `TrainingReadinessDTO_*`
- `MetricsAcuteTrainingLoad_*`
- `RunRacePredictions_*`
- `CyclingAbility_*`
- `EnduranceScore_*`
- `HillScore_*`

**Exported files:** 53

## What this family contains

Garmin-generated assessments, scores, predictions, and derived metrics, including:

- training readiness
- acute training load / ACWR
- race predictions
- cycling ability
- endurance score
- hill score

## Important principle

These should **not automatically be used as ground-truth labels** for our own anomaly-detection model.

They may still be useful for:

- comparison with our own results
- contextual information
- sanity checks
- discussing differences between Garmin's assessments and our approach

## Decision

- [ ] KEEP
- [ ] SUPPORTING
- [X] DROP

## Rationale

These metrics are primarily Garmin-generated assessments and conclusions.

The thesis will focus on deriving its own conclusions from the underlying data rather than reproducing or relying on Garmin's proprietary assessments. Therefore, these metrics are not required for the main analytical pipeline.

They may still be useful in the future for comparison purposes, but they are outside the current scope.

---

# 8. Low-Level / Other

**Category:** `low_level`  
**Exported files:** 44

## What this family contains

Remaining JSON files that do not currently belong to the main analytical families.

Examples include:

- account/configuration
- profile
- device
- metadata-type files
- other exports not currently identified as core training, recovery, performance, or environmental measurements

## What to determine

- Is any file actually useful to the thesis?
- Is any file required to interpret another dataset?
- Is anything here an important metadata/identifier source?
- Can the rest safely be excluded from the analytical pipeline?

## Decision

- [ ] KEEP
- [ ] SUPPORTING
- [X] DROP

## Rationale

The majority of this category consists of account, configuration, profile, device, and application-related information that is not directly relevant to the analytical objectives of the thesis.

No currently identified information in this category is necessary for the main analytical pipeline, so it can be excluded from the current scope.

If a specific metadata or identifier file becomes necessary later for interpreting the selected datasets, it can be reconsidered at that stage.

---

# Final Category Summary

| Category | Decision | Rationale |
|---|---|---|
| `daily_wellness` | [X] KEEP / [ ] SUPPORTING / [ ] DROP | Core daily measurements |
| `sleep` | [X] KEEP / [ ] SUPPORTING / [ ] DROP | Important recovery measurements |
| `hydration` | [ ] KEEP / [X] SUPPORTING / [ ] DROP | Limited and partly estimated information |
| `health_status` | [ ] KEEP / [ ] SUPPORTING / [X] DROP | Garmin-derived health-status information |
| `performance` | [ ] KEEP / [X] SUPPORTING / [ ] DROP | Useful contextual performance estimates |
| `environmental` | [ ] KEEP / [ ] SUPPORTING / [X] DROP | Outside current thesis scope |
| `garmin_derived` | [ ] KEEP / [ ] SUPPORTING / [X] DROP | Garmin assessments not needed for our own analysis |
| `low_level` | [ ] KEEP / [ ] SUPPORTING / [X] DROP | Mostly account/configuration/application data |

---