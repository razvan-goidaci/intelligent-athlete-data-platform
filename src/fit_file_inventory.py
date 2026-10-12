
from pathlib import Path
from collections import Counter
from fitparse import FitFile
import json

DATA_DIR = Path("data/raw/activity_fit_files")
OUTPUT_DIR = Path("data/processed")


def fit_file_to_dict(file_path):
    fit_file = FitFile(str(file_path))

    inventory = {
        "file": file_path.name,
        "message_counts": {},
        "fields": {}
    }

    message_counts = Counter(
        message.name for message in fit_file.get_messages()
    )
    inventory["message_counts"] = dict(message_counts)

    fields_dir = {}

    for message in fit_file.get_messages():
        if message.name in fields_dir:
            continue

        fields_dir[message.name] = {}

        for field in message:
            fields_dir[message.name][field.name] = (
                type(field.value).__name__
            )

    inventory["fields"] = fields_dir

    return inventory


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fit_files = sorted(DATA_DIR.rglob("*.fit"))

    if not fit_files:
        print(f"No FIT files found in: {DATA_DIR.resolve()}")
        return

    for file_path in fit_files:
        inventory = fit_file_to_dict(file_path)

        output_path = OUTPUT_DIR / file_path.with_suffix(".json").name

        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(inventory, output_file, indent=2)

        print(f"Inventory saved to: {output_path}")

    print(f"\nFinished. Processed {len(fit_files)} FIT files.")


if __name__ == "__main__":
    main()
