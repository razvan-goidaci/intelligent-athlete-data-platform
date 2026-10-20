import shutil
import json
from pathlib import Path

CATEGORIES = {
    "daily_wellness": ["UDSFile_"],
    "sleep": ["_sleepData.json"],
    "hydration": ["HydrationLogFile_"],
    "health_status": ["_healthStatusData.json"],
    "performance": [
        "ActivityVo2Max_",
        "MetricsMaxMetData_",
        "fitnessAgeData",
    ],
    "environmental": ["MetricsHeatAltitudeAcclimation_"],
    "garmin_derived": [
        "TrainingReadinessDTO_",
        "MetricsAcuteTrainingLoad_",
        "RunRacePredictions_",
        "CyclingAbility_",
        "EnduranceScore_",
        "HillScore_",
    ],
}

json_dir = Path("data/raw/json")
files = list(json_dir.rglob("*.json"))

for file in files:
    matched_category = None

    for category, patterns in CATEGORIES.items():
        if any(pattern in file.name for pattern in patterns):
            matched_category = category
            break

    if matched_category:
        destination_dir = json_dir / matched_category
    else:
        destination_dir = json_dir / "low_level"

    destination_dir.mkdir(exist_ok=True)

    destination = destination_dir / file.name
    shutil.move(file, destination)

    print(f"Moved: {file.name} -> {destination_dir.name}/")


SOURCE_DIR = Path("data/raw/json")
OUTPUT_DIR = Path("data/processed/json_formatted")

for file in SOURCE_DIR.rglob("*.json"):
    relative_path = file.relative_to(SOURCE_DIR)
    output_file = OUTPUT_DIR / relative_path

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(file, "r", encoding="utf-8") as source:
        data = json.load(source)

    with open(output_file, "w", encoding="utf-8") as output:
        json.dump(
            data,
            output,
            indent=4,
            ensure_ascii=False
        )

    print(f"Formatted: {relative_path}")

print("\nFormatting complete.")