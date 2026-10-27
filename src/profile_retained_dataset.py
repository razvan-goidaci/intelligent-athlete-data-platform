from pathlib import Path
from datetime import datetime, time
import json
import math

from fitparse import FitFile


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed/profiling")
OUTPUT_FILE = OUTPUT_DIR / "retained_data_profile.json"

RETAINED_FIT_TYPES = {
    "activity",
    "monitoring_b",
    "metrics",
    "sleep",
    "hrv_status",
    "44",
    "49",
    "68",
}

RETAINED_JSON_PATTERNS = {
    "daily_wellness": ("UDSFile_",),
    "sleep": ("_sleepData.json",),
    "performance": (
        "ActivityVo2Max_",
        "MetricsMaxMetData_",
        "fitnessAgeData",
    ),
}

EXCLUDED_JSON_PATTERNS = {
    "hydration": ("HydrationLogFile_",),
    "health_status": ("_healthStatusData.json",),
    "environmental": ("MetricsHeatAltitudeAcclimation_",),
    "garmin_derived": (
        "TrainingReadinessDTO_",
        "MetricsAcuteTrainingLoad_",
        "RunRacePredictions_",
        "CyclingAbility_",
        "EnduranceScore_",
        "HillScore_",
    ),
}


def is_missing(value):
    return value is None or (
        isinstance(value, float) and math.isnan(value)
    )


def safe_value(value):
    if isinstance(value, (datetime, time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def create_field_profile():
    return {
        "files_present": 0,
        "value_count": 0,
        "missing_count": 0,
        "observed_types": set(),
        "examples": [],
        "minimum": None,
        "maximum": None,
        "earliest": None,
        "latest": None,
        "distinct_values": set(),
    }


def update_field_profile(profile, value):
    profile["observed_types"].add(type(value).__name__)

    if is_missing(value):
        profile["missing_count"] += 1
        return

    profile["value_count"] += 1
    value = safe_value(value)

    if len(profile["examples"]) < 5 and value not in profile["examples"]:
        profile["examples"].append(value)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isfinite(float(value)):
            if profile["minimum"] is None:
                profile["minimum"] = value
            else:
                profile["minimum"] = min(profile["minimum"], value)

            if profile["maximum"] is None:
                profile["maximum"] = value
            else:
                profile["maximum"] = max(profile["maximum"], value)

    if isinstance(value, str):
        try:
            datetime.fromisoformat(value)
            if profile["earliest"] is None or value < profile["earliest"]:
                profile["earliest"] = value
            if profile["latest"] is None or value > profile["latest"]:
                profile["latest"] = value
        except ValueError:
            pass

    if value is not None and len(profile["distinct_values"]) < 100:
        profile["distinct_values"].add(
            json.dumps(value, sort_keys=True)
        )


def finalize_field_profile(profile):
    profile["observed_types"] = sorted(profile["observed_types"])
    profile["distinct_values"] = [
        json.loads(value)
        for value in sorted(profile["distinct_values"])
    ]
    profile["distinct_values_sample_size"] = len(
        profile["distinct_values"]
    )
    return profile


def normalize_fit_type(value):
    if value is None:
        return None

    value = str(value).lower()

    aliases = {
        "activity": "activity",
        "monitoring_b": "monitoring_b",
        "metrics": "metrics",
        "sleep": "sleep",
        "hrv_status": "hrv_status",
        "hrv status": "hrv_status",
        "44": "44",
        "49": "49",
        "68": "68",
    }

    return aliases.get(value, value)


def get_fit_type(file_path):
    fit_file = FitFile(str(file_path))

    for message in fit_file.get_messages("file_id"):
        return normalize_fit_type(
            message.get_value("type")
        )

    return None


def profile_fit_file(file_path):
    fit_file = FitFile(str(file_path))
    messages = {}

    for message in fit_file.get_messages():
        message_name = message.name

        if message_name not in messages:
            messages[message_name] = {
                "message_count": 0,
                "fields": {},
            }

        messages[message_name]["message_count"] += 1

        for field in message:
            field_name = field.name

            if field_name not in messages[message_name]["fields"]:
                messages[message_name]["fields"][field_name] = (
                    create_field_profile()
                )

            update_field_profile(
                messages[message_name]["fields"][field_name],
                field.value,
            )

    return messages


def merge_fit_profile(target, source):
    for message_name, message_data in source.items():
        if message_name not in target:
            target[message_name] = {
                "files_present": 0,
                "message_count": 0,
                "fields": {},
            }

        target_message = target[message_name]
        target_message["files_present"] += 1
        target_message["message_count"] += message_data["message_count"]

        for field_name, field_data in message_data["fields"].items():
            if field_name not in target_message["fields"]:
                target_message["fields"][field_name] = (
                    create_field_profile()
                )

            target_field = target_message["fields"][field_name]
            target_field["files_present"] += 1
            target_field["value_count"] += field_data["value_count"]
            target_field["missing_count"] += field_data["missing_count"]
            target_field["observed_types"].update(
                field_data["observed_types"]
            )

            for example in field_data["examples"]:
                if (
                    example not in target_field["examples"]
                    and len(target_field["examples"]) < 5
                ):
                    target_field["examples"].append(example)

            if field_data["minimum"] is not None:
                if target_field["minimum"] is None:
                    target_field["minimum"] = field_data["minimum"]
                else:
                    target_field["minimum"] = min(
                        target_field["minimum"],
                        field_data["minimum"],
                    )

            if field_data["maximum"] is not None:
                if target_field["maximum"] is None:
                    target_field["maximum"] = field_data["maximum"]
                else:
                    target_field["maximum"] = max(
                        target_field["maximum"],
                        field_data["maximum"],
                    )

            if field_data["earliest"] is not None:
                if (
                    target_field["earliest"] is None
                    or field_data["earliest"] < target_field["earliest"]
                ):
                    target_field["earliest"] = field_data["earliest"]

            if field_data["latest"] is not None:
                if (
                    target_field["latest"] is None
                    or field_data["latest"] > target_field["latest"]
                ):
                    target_field["latest"] = field_data["latest"]

            for value in field_data["distinct_values"]:
                if len(target_field["distinct_values"]) >= 100:
                    break
                target_field["distinct_values"].add(
                    json.dumps(value, sort_keys=True)
                )


def profile_fit_directory(data_dir):
    files = sorted(data_dir.rglob("*.fit"))

    profile = {
        "files_scanned": len(files),
        "files_retained": 0,
        "files_excluded": 0,
        "types": {},
        "messages": {},
    }

    for index, file_path in enumerate(files, start=1):
        fit_type = get_fit_type(file_path)

        profile["types"][fit_type or "unknown"] = (
            profile["types"].get(fit_type or "unknown", 0) + 1
        )

        if fit_type not in RETAINED_FIT_TYPES:
            profile["files_excluded"] += 1
            continue

        profile["files_retained"] += 1

        merge_fit_profile(
            profile["messages"],
            profile_fit_file(file_path),
        )

        if index % 1000 == 0:
            print(f"FIT files scanned: {index}/{len(files)}")

    for message in profile["messages"].values():
        for field in message["fields"].values():
            finalize_field_profile(field)

    return profile


def classify_json_file(file_path):
    filename = file_path.name

    for family, patterns in RETAINED_JSON_PATTERNS.items():
        if any(pattern in filename for pattern in patterns):
            return family

    for family, patterns in EXCLUDED_JSON_PATTERNS.items():
        if any(pattern in filename for pattern in patterns):
            return f"excluded:{family}"

    return None


def profile_json_value(fields, path, value):
    if isinstance(value, dict):
        for name, nested_value in value.items():
            nested_path = f"{path}.{name}" if path else name
            profile_json_value(fields, nested_path, nested_value)
        return

    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                for name, nested_value in item.items():
                    profile_json_value(
                        fields,
                        f"{path}[].{name}",
                        nested_value,
                    )
            else:
                field = fields.setdefault(
                    path,
                    create_field_profile(),
                )
                update_field_profile(field, item)
        return

    field = fields.setdefault(
        path,
        create_field_profile(),
    )
    update_field_profile(field, value)


def profile_json_file(file_path):
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    records = [data] if isinstance(data, dict) else data

    result = {
        "file": str(file_path.relative_to(DATA_DIR)),
        "family": classify_json_file(file_path),
        "structure": type(data).__name__,
        "records": len(records) if isinstance(records, list) else 0,
        "fields": {},
    }

    fields = {}

    for record in records:
        if isinstance(record, dict):
            for name, value in record.items():
                profile_json_value(fields, name, value)

    for name, field in fields.items():
        field["files_present"] = 1
        result["fields"][name] = finalize_field_profile(field)

    return result


def profile_json_directory(data_dir):
    files = sorted(data_dir.rglob("*.json"))

    profile = {
        "files_scanned": len(files),
        "files_retained": 0,
        "files_excluded": 0,
        "files_unclassified": 0,
        "datasets": [],
    }

    for file_path in files:
        family = classify_json_file(file_path)

        if family is None:
            profile["files_unclassified"] += 1
            continue

        if family.startswith("excluded:"):
            profile["files_excluded"] += 1
            continue

        profile["files_retained"] += 1
        profile["datasets"].append(
            profile_json_file(file_path)
        )

    return profile


def build_profile():
    print("Profiling FIT data...")
    fit_profile = profile_fit_directory(
        DATA_DIR / "fit"
    )

    print("Profiling JSON data...")
    json_profile = profile_json_directory(
        DATA_DIR / "json"
    )

    return {
        "scope": {
            "retained_fit_types": sorted(RETAINED_FIT_TYPES),
            "retained_json_families": sorted(
                RETAINED_JSON_PATTERNS
            ),
            "hydration_excluded": True,
        },
        "fit": fit_profile,
        "json": json_profile,
    }


def main():
    profile = build_profile()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            profile,
            file,
            indent=2,
        )

    print(f"Profile saved to: {OUTPUT_FILE}")
    print("Profiling completed.")


if __name__ == "__main__":
    main()