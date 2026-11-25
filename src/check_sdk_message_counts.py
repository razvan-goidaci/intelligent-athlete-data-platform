from garmin_fit_sdk import Decoder, Stream
from pathlib import Path
from collections import Counter

retained_file_types = {
    "activity",
    "monitoring_b",
    49,
    68
}

total = Counter()

fit_dir = Path("data/raw/fit")
fit_files = sorted(fit_dir.glob("*.fit"))

for path in fit_files:
    
    stream = Stream.from_file(str(path))
    decoder  = Decoder(stream)

    messages, errors = decoder.read(
        apply_scale_and_offset = True,
        convert_datetimes_to_dates = True,
        convert_types_to_strings = True,
        expand_sub_fields = True,
        expand_components = False,
        merge_heart_rates = False
    )

    file_type = messages["file_id_mesgs"][0]["type"]
    if file_type in retained_file_types:
        for key, value in messages.items():
            total[key] += len(value)

for key, count in sorted(total.items()):
    print(f"{key}: {count}")


