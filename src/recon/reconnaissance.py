from pathlib import Path
from collections import Counter, defaultdict
import json

from fitparse import FitFile


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed/reconnaissance")
OUTPUT_FILE = OUTPUT_DIR / "reconnaissance.json"


def inspect_fit_file(file_path):
    """Inspect one FIT file and collect message counts and observed field types."""
    fit_file = FitFile(str(file_path))

    message_counts = Counter()
    fields = defaultdict(
        lambda: defaultdict(
            lambda: {
                "files_present": 0,
                "message_count": 0,
                "observed_types": [],
            }
        )
    )

    messages_seen = set()

    for message in fit_file.get_messages():
        message_name = message.name
        message_counts[message_name] += 1

        for field in message:
            field_name = field.name
            field_type = type(field.value).__name__

            field_data = fields[message_name][field_name]

            if field_type not in field_data["observed_types"]:
                field_data["observed_types"].append(field_type)

            field_data["message_count"] += 1

        messages_seen.add(message_name)

    for message_name in messages_seen:
        for field_name in fields[message_name]:
            fields[message_name][field_name]["files_present"] += 1

    return {
        "file": file_path.name,
        "message_counts": dict(message_counts),
        "fields": {
            message_name: dict(message_fields)
            for message_name, message_fields in fields.items()
        },
    }


def inspect_fit_directory(data_dir):
    """Inspect all FIT files and combine their message and field information."""
    fit_files = sorted(data_dir.rglob("*.fit"))

    profile = {
        "files": len(fit_files),
        "messages": {},
    }

    for file_path in fit_files:
        result = inspect_fit_file(file_path)

        for message_name, message_count in result["message_counts"].items():
            if message_name not in profile["messages"]:
                profile["messages"][message_name] = {
                    "files_present": 0,
                    "total_messages": 0,
                    "fields": {},
                }

            message_profile = profile["messages"][message_name]
            message_profile["files_present"] += 1
            message_profile["total_messages"] += message_count

            for field_name, field_data in result["fields"].get(
                message_name, {}
            ).items():
                if field_name not in message_profile["fields"]:
                    message_profile["fields"][field_name] = {
                        "files_present": 0,
                        "observed_types": [],
                    }

                profile_field = message_profile["fields"][field_name]

                for observed_type in field_data["observed_types"]:
                    if observed_type not in profile_field["observed_types"]:
                        profile_field["observed_types"].append(observed_type)

                profile_field["files_present"] += 1

    return profile


def inspect_json_file(file_path):
    """Inspect one JSON file and record its top-level structure and fields."""
    try:
        with file_path.open("r", encoding="utf-8") as input_file:
            data = json.load(input_file)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        return {
            "file": file_path.name,
            "structure": "invalid",
            "fields": [],
            "error": str(error),
        }

    if isinstance(data, dict):
        structure = "object"
        fields = list(data.keys())

    elif isinstance(data, list):
        structure = "array"

        if data and isinstance(data[0], dict):
            fields = list(data[0].keys())
        else:
            fields = []

    else:
        structure = type(data).__name__
        fields = []

    return {
        "file": file_path.name,
        "structure": structure,
        "fields": fields,
    }


def inspect_json_directory(data_dir):
    """Inspect all JSON files and record their basic structural information."""
    json_files = sorted(data_dir.rglob("*.json"))

    return {
        "files": len(json_files),
        "datasets": [
            inspect_json_file(file_path)
            for file_path in json_files
        ],
    }


def build_reconnaissance(data_dir=DATA_DIR):
    """Build a combined reconnaissance report for FIT and JSON source data."""
    return {
        "fit": inspect_fit_directory(data_dir / "fit"),
        "json": inspect_json_directory(data_dir / "json"),
    }


def save_reconnaissance(reconnaissance, output_file=OUTPUT_FILE):
    """Save the reconnaissance report as a JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(reconnaissance, file, indent=2)

    print(f"Reconnaissance saved to: {output_file}")


def main():
    """Run the complete raw-data reconnaissance process."""
    reconnaissance = build_reconnaissance()
    save_reconnaissance(reconnaissance)


if __name__ == "__main__":
    main()