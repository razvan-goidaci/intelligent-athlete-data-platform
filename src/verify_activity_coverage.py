from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json
import re

from fitparse import FitFile


DATA_DIR = Path("data/raw")
SOURCE_ZIP = DATA_DIR / "GarminExport.zip"
OUTPUT_DIR = Path("data/processed/validation")
OUTPUT_FILE = OUTPUT_DIR / "activity_coverage.json"

NEAR_MATCH_SECONDS = 300
MIN_GAP_DAYS = 30


def read_fit_summary(file_path):
    """Read the FIT type, creation time and any activity session start times."""
    fit_file = FitFile(str(file_path))
    fit_type = None
    time_created = None

    for message in fit_file.get_messages("file_id"):
        fit_type = str(message.get_value("type"))
        time_created = message.get_value("time_created")
        break

    session_starts = []

    if fit_type == "activity":
        for message in FitFile(str(file_path)).get_messages("session"):
            start_time = message.get_value("start_time")
            if start_time is not None:
                session_starts.append(start_time)

    return {
        "file": file_path.name,
        "type": fit_type,
        "time_created": time_created,
        "session_starts": session_starts,
    }


def read_fit_summaries(data_dir):
    """Read a summary of every FIT file, using all CPU cores because parsing is slow."""
    files = sorted((data_dir / "fit").glob("*.fit"))

    with ProcessPoolExecutor() as pool:
        return list(pool.map(read_fit_summary, files, chunksize=64))


def load_summarized_activities(data_dir):
    """Load the activity list from the summarizedActivities JSON files."""
    activities = []

    for file_path in sorted((data_dir / "json").glob("*summarizedActivities*.json")):
        with file_path.open("r", encoding="utf-8") as file:
            activities.extend(json.load(file)[0]["summarizedActivitiesExport"])

    return activities


def activity_start(activity):
    """Convert the JSON start time, in epoch milliseconds, to FIT's naive UTC datetimes."""
    start = datetime.fromtimestamp(
        activity["beginTimestamp"] / 1000,
        timezone.utc,
    )
    return start.replace(tzinfo=None, microsecond=0)


def match_activities(activities, fit_starts):
    """Split JSON activities into exact, near and no FIT match by start time."""
    exact = []
    near = []
    unmatched = []

    for activity in activities:
        start = activity_start(activity)

        if start in fit_starts:
            exact.append(activity)
        elif any(
            abs((fit_start - start).total_seconds()) <= NEAR_MATCH_SECONDS
            for fit_start in fit_starts
        ):
            near.append(activity)
        else:
            unmatched.append(activity)

    return exact, near, unmatched


def count_by_month(activities):
    counts = Counter(
        activity_start(activity).strftime("%Y-%m")
        for activity in activities
    )
    return dict(sorted(counts.items()))


def find_gaps(times, min_days=MIN_GAP_DAYS):
    """Find periods of at least min_days between consecutive times."""
    ordered = sorted(times)
    return [
        {
            "after": str(earlier.date()),
            "before": str(later.date()),
            "days": (later - earlier).days,
        }
        for earlier, later in zip(ordered, ordered[1:])
        if later - earlier >= timedelta(days=min_days)
    ]


def fit_gaps_by_type(summaries):
    """Find long gaps in file creation times for each FIT type."""
    times = {}

    for summary in summaries:
        if summary["time_created"] is not None:
            times.setdefault(summary["type"], []).append(summary["time_created"])

    return {
        fit_type: find_gaps(type_times)
        for fit_type, type_times in sorted(times.items())
    }


def uploaded_file_archives(source_zip):
    """Count the FIT files in each numbered UploadedFiles archive in the export."""
    archives = {}

    with ZipFile(source_zip, "r") as zip_file:
        for item in zip_file.infolist():
            part = re.search(r"UploadedFiles.*_(Part\d+)\.zip$", item.filename)

            if part:
                with ZipFile(BytesIO(zip_file.read(item))) as nested_zip:
                    archives[part.group(1)] = sum(
                        name.lower().endswith(".fit")
                        for name in nested_zip.namelist()
                    )

    return dict(sorted(archives.items()))


def build_report(data_dir=DATA_DIR, source_zip=SOURCE_ZIP):
    """Compare the activity list in the JSON files with the FIT files in the export."""
    summaries = read_fit_summaries(data_dir)
    activities = load_summarized_activities(data_dir)

    fit_starts = {
        start
        for summary in summaries
        for start in summary["session_starts"]
    }
    exact, near, unmatched = match_activities(activities, fit_starts)

    return {
        "fit_files": len(summaries),
        "activity_fit_sessions": len(fit_starts),
        "json_activities": len(activities),
        "exact_start_matches": len(exact),
        "near_start_matches": len(near),
        "no_fit_match": len(unmatched),
        "no_fit_match_by_month": count_by_month(unmatched),
        "uploaded_file_archives": uploaded_file_archives(source_zip),
        "fit_gaps_by_type": fit_gaps_by_type(summaries),
    }


def main():
    """Build, save and print the activity coverage report."""
    report = build_report()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(json.dumps(report, indent=2))
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
