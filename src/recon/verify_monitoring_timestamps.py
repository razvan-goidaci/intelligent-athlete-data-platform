from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import json

from fitparse import FitFile


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed/validation")
OUTPUT_FILE = OUTPUT_DIR / "monitoring_timestamps.json"

LOW_16_BITS = 0xFFFF
ROLLOVER_SECONDS = 65536
SECONDS_PER_DAY = 86400
HIDDEN_TEST_PASS_RATE = 0.999


def reconstruct_time(reference, timestamp_16):
    """Return the first FIT time at or after reference whose low 16 bits match timestamp_16."""
    return reference + ((timestamp_16 - reference) & LOW_16_BITS)


def read_file_header(fit_file):
    """Return the FIT file type and its raw creation time."""
    for message in fit_file.get_messages("file_id"):
        return (
            str(message.get_value("type")),
            message.get("time_created").raw_value,
        )

    return None, None


def check_file(file_path):
    """Reconstruct the monitoring times in one FIT file and count the check results."""
    fit_file = FitFile(str(file_path))
    fit_type, time_created = read_file_header(fit_file)
    counts = Counter()

    if fit_type != "monitoring_b":
        return counts

    counts["files"] += 1
    reference = None

    for message in FitFile(str(file_path)).get_messages("monitoring"):
        full_field = message.get("timestamp")
        short_field = message.get("timestamp_16")

        if full_field is not None:
            current = full_field.raw_value
            counts["full_timestamps"] += 1

            if reference is not None:
                counts["hidden_test_total"] += 1
                hidden = reconstruct_time(reference, current & LOW_16_BITS)
                counts["hidden_test_exact"] += hidden == current

                # An earlier reconstructed time must not pass this real timestamp.
                counts["full_time_before_previous"] += current < reference

        elif short_field is not None:
            counts["timestamp_16_total"] += 1

            if reference is None:
                counts["timestamp_16_unresolvable"] += 1
                continue

            current = reconstruct_time(reference, short_field.raw_value)
            counts["timestamp_16_reconstructed"] += 1

        else:
            counts["no_time_field"] += 1
            continue

        counts["outside_one_day_of_file_creation"] += (
            abs(current - time_created) > SECONDS_PER_DAY
        )
        reference = current

    return counts


def build_report(data_dir=DATA_DIR):
    """Run the timestamp checks across all FIT files and combine the results."""
    files = sorted((data_dir / "fit").glob("*.fit"))
    totals = Counter()

    with ProcessPoolExecutor() as pool:
        for counts in pool.map(check_file, files, chunksize=64):
            totals.update(counts)

    pass_rate = totals["hidden_test_exact"] / totals["hidden_test_total"]

    return {
        "rollover_seconds": ROLLOVER_SECONDS,
        "counts": dict(sorted(totals.items())),
        "hidden_test_pass_rate": pass_rate,
        "hidden_test_passed": pass_rate >= HIDDEN_TEST_PASS_RATE,
    }


def main():
    """Build, save and print the monitoring timestamp report."""
    report = build_report()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(json.dumps(report, indent=2))
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
