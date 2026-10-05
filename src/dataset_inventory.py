from pathlib import Path
from collections import Counter
from zipfile import ZipFile

DATA_DIR = Path("data/raw/GarminExport")

for zip_file in DATA_DIR.rglob("*.zip"):
    print(f"\n--- {zip_file.name} ---")

    with ZipFile(zip_file) as archive:
        counter = Counter(file[-3:] for file in archive.namelist())
        for extension, count in counter.items():
            if extension == "fit":
                print(f"For .zip file {zip_file.name}, there are {count} .fit files.")