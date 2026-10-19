from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import shutil
from fitparse import FitFile

DATA_DIR = Path("data/raw/GarminExport.zip")
OUTPUT_DIR = DATA_DIR.parent


def count_total_items(data_dir):
    """Count all files to be extracted, including nested ZIP contents."""

    total_files = 0

    with ZipFile(data_dir) as archive:
        for item in archive.namelist():
            if item.endswith("/"):
                continue

            if item.lower().endswith(".zip"):
                with archive.open(item) as nested_file:
                    nested_data = nested_file.read()

                total_files += count_total_items(BytesIO(nested_data))
            else:
                total_files += 1

    return total_files


def extract_files(data_dir=DATA_DIR):
    """Extract all files from Garmin export."""

    total_items = count_total_items(data_dir)
    processed = 0

    def extract_archive(archive):
        nonlocal processed

        for item in archive.namelist():
            if item.endswith("/"):
                continue

            if item.lower().endswith(".zip"):
                with archive.open(item) as nested_file:
                    nested_data = nested_file.read()

                with ZipFile(BytesIO(nested_data)) as nested_archive:
                    extract_archive(nested_archive)

            else:
                new_dir = Path(item).suffix.lstrip(".")
                output_dir = OUTPUT_DIR / new_dir
                output_dir.mkdir(parents=True, exist_ok=True)

                with archive.open(item) as source:
                    output_file = output_dir / Path(item).name

                    with open(output_file, "wb") as target:
                        target.write(source.read())

                processed += 1
                percentage = processed / total_items * 100
                print(f"\rExtracting: {percentage:.1f}%", end="")

    with ZipFile(data_dir) as archive:
        extract_archive(archive)

    print(f"\nExtraction complete. Processed {processed} of {total_items} files.")

def organise_fit_files(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    """Organise extracted FIT files into a dedicated directory."""
    fit_files = list(data_dir.rglob("*.fit"))
    if not fit_files:
        print(f"No FIT files found in: {data_dir.resolve()}")
        return

    for fit_file in fit_files:
        fit_file_data = FitFile(str(fit_file))
        file_id_messages = fit_file_data.get_messages("file_id")

        fit_type = next(
            (message.get_value("type") for message in file_id_messages),
            None,
        )

        new_dir = (
            output_dir / f"{fit_type}_fit_file"
            if fit_type
            else output_dir / "unknown_fit_file"
        )

        new_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(fit_file, new_dir / fit_file.name)

    print(f"\nFinished organising {len(fit_files)} FIT files.")

extract_files()
organise_fit_files(Path("data/raw/fit"), Path("data/raw"))