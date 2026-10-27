from pathlib import Path
from zipfile import ZipFile
from io import BytesIO


DATA_DIR = Path("data/raw/GarminExport.zip")
OUTPUT_DIR = DATA_DIR.parent


def count_total_items(zip_file):
    """Count all files contained in a ZIP, including files inside nested ZIPs."""
    total = 0

    for item in zip_file.infolist():
        if item.is_dir():
            continue

        total += 1

        if item.filename.lower().endswith(".zip"):
            nested_data = zip_file.read(item)
            with ZipFile(BytesIO(nested_data)) as nested_zip:
                total += count_total_items(nested_zip)

    return total


def extract_zip_contents(zip_file, output_dir):
    """Extract files from a ZIP and recursively extract any nested ZIP archives."""
    for item in zip_file.infolist():
        if item.is_dir():
            continue

        filename = Path(item.filename)

        if filename.name == "":
            continue

        if filename.suffix.lower() == ".zip":
            nested_data = zip_file.read(item)

            with ZipFile(BytesIO(nested_data)) as nested_zip:
                extract_zip_contents(nested_zip, output_dir)

            continue

        suffix = filename.suffix.lower().lstrip(".")

        if not suffix:
            suffix = "other"

        destination_dir = output_dir / suffix
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination = destination_dir / filename.name

        with destination.open("wb") as output_file:
            output_file.write(zip_file.read(item))


def extract_files(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    """Extract the Garmin export into raw data directories without modifying the source ZIP."""
    if not data_dir.exists():
        print(f"Source ZIP not found: {data_dir.resolve()}")
        return

    with ZipFile(data_dir, "r") as zip_file:
        total_items = count_total_items(zip_file)

        print(f"Total files in archive: {total_items}")

        extract_zip_contents(zip_file, output_dir)

    print(f"Extraction completed: {output_dir.resolve()}")


if __name__ == "__main__":
    extract_files()