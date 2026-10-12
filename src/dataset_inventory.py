from pathlib import Path
from collections import Counter
from zipfile import ZipFile
from fitparse import FitFile

DATA_DIR = Path("data/raw/GarminExport")
ACTIVITY_DIR = Path("data/raw/activity_fit_files")


def list_fit_files_in_zip(data_dir=DATA_DIR):
    """Count FIT files in each ZIP archive."""
    for zip_path in data_dir.rglob("*.zip"):
        with ZipFile(zip_path) as archive:
            fit_count = sum(
                name.lower().endswith(".fit")
                for name in archive.namelist()
            )
            print(f"{zip_path.name}: {fit_count} FIT files")


def extract_sample_fit_file(data_dir=DATA_DIR, sample_number=10):
    """Extract the Nth FIT file from each ZIP archive as a sample."""
    for zip_path in data_dir.rglob("*.zip"):
        with ZipFile(zip_path) as archive:
            fit_names = [
                name for name in archive.namelist()
                if name.lower().endswith(".fit")
            ]

            if len(fit_names) >= sample_number:
                member_name = fit_names[sample_number - 1]
                print(f"{zip_path.name}: extracting sample {sample_number}: {member_name}")
                archive.extract(member_name, path="data/raw")
            else:
                print(f"{zip_path.name}: only {len(fit_names)} FIT files")


def extract_activity_fit_files(
    data_dir=DATA_DIR,
    output_dir=ACTIVITY_DIR,
    max_files=1500,
):
    """Find and extract activity-type FIT files from ZIP archives."""
    output_dir.mkdir(parents=True, exist_ok=True)
    checked = 0
    extracted = 0

    for zip_path in data_dir.rglob("*.zip"):
        with ZipFile(zip_path) as archive:
            for member_name in archive.namelist():
                if not member_name.lower().endswith(".fit"):
                    continue

                checked += 1
                if checked > max_files:
                    print(f"Reached scan limit of {max_files} FIT files.")
                    print(f"Checked: {checked - 1}; extracted: {extracted}")
                    return

                with archive.open(member_name) as fit_stream:
                    fit_file = FitFile(fit_stream)
                    file_id_messages = fit_file.get_messages("file_id")
                    fit_type = next(
                        (message.get_value("type") for message in file_id_messages),
                        None,
                    )

                if fit_type == "activity":
                    archive.extract(member_name, path=output_dir)
                    extracted += 1
                    print(f"Extracted activity FIT: {member_name}")

    print(f"Checked: {checked}; extracted: {extracted}")


def count_fit_file_types(data_dir=DATA_DIR):
    """Count FIT file types across ZIP archives."""
    fit_type_counts = Counter()
    files_checked = 0

    for zip_path in data_dir.rglob("*.zip"):
        with ZipFile(zip_path) as archive:
            for member_name in archive.namelist():
                if not member_name.lower().endswith(".fit"):
                    continue

                files_checked += 1

                with archive.open(member_name) as fit_stream:
                    fit_file = FitFile(fit_stream)
                    file_id_messages = fit_file.get_messages("file_id")
                    fit_type = next(
                        (message.get_value("type") for message in file_id_messages),
                        None,
                    )

                fit_type_counts[fit_type] += 1

    print(f"Checked {files_checked} FIT files.")
    print("FIT file type counts:")
    for fit_type, count in fit_type_counts.most_common():
        print(f"  {fit_type}: {count}")


if __name__ == "__main__":
    count_fit_file_types()
