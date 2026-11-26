from pathlib import Path
from collections import Counter
import json


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed/inventory")
OUTPUT_FILE = OUTPUT_DIR / "dataset_inventory.json"


def count_files_by_extension(data_dir):
    """Count files in the raw data directory grouped by file extension."""
    counts = Counter()

    for file_path in data_dir.rglob("*"):
        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()

        if extension:
            counts[extension] += 1
        else:
            counts["no_extension"] += 1

    return dict(sorted(counts.items()))


def count_files_by_directory(data_dir):
    """Count files grouped by their top-level raw data directory."""
    counts = Counter()

    for file_path in data_dir.rglob("*"):
        if not file_path.is_file():
            continue

        relative_path = file_path.relative_to(data_dir)

        if relative_path.parts:
            counts[relative_path.parts[0]] += 1

    return dict(sorted(counts.items()))


def inventory_json_files(data_dir):
    """Collect basic structural information about JSON files without interpreting their meaning."""
    inventory = []

    for file_path in sorted(data_dir.rglob("*.json")):
        try:
            with file_path.open("r", encoding="utf-8") as input_file:
                data = json.load(input_file)

            if isinstance(data, dict):
                structure = "object"
                keys = list(data.keys())
            elif isinstance(data, list):
                structure = "array"
                keys = []

                if data and isinstance(data[0], dict):
                    keys = list(data[0].keys())
            else:
                structure = type(data).__name__
                keys = []

            inventory.append(
                {
                    "file": str(file_path.relative_to(data_dir)),
                    "structure": structure,
                    "keys": keys,
                }
            )

        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            inventory.append(
                {
                    "file": str(file_path.relative_to(data_dir)),
                    "structure": "invalid",
                    "keys": [],
                    "error": str(error),
                }
            )

    return inventory


def build_inventory(data_dir=DATA_DIR):
    """Build a single inventory describing the files and basic structures in the raw dataset."""
    return {
        "data_directory": str(data_dir),
        "files_by_extension": count_files_by_extension(data_dir),
        "files_by_directory": count_files_by_directory(data_dir),
        "json_files": inventory_json_files(data_dir / "json"),
    }


def save_inventory(inventory, output_file=OUTPUT_FILE):
    """Save the dataset inventory as a JSON report."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(inventory, file, indent=2)

    print(f"Inventory saved to: {output_file}")


def main():
    """Build and save the raw dataset inventory."""
    inventory = build_inventory()
    save_inventory(inventory)


if __name__ == "__main__":
    main()