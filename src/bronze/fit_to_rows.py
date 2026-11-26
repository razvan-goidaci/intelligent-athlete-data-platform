from garmin_fit_sdk import Decoder, Stream, Profile
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

BRONZE_FIT_TABLES = {
    "session", "lap", "record", "activity", "event",
    "monitoring", "stress_level", "respiration_rate",
    "sleep_level", "sleep_assessment", "hrv_value", "hrv_status_summary",
    "file_id", "device_info", "timestamp_correlation",
}

# In Profile["types"], but really numbers with a few named special values.
NUMERIC_PROFILE_TYPES = {
    "date_time",
    "local_date_time",
    "message_index",
    "left_right_balance",
    "left_right_balance_100",
}

RETAINED_FILE_TYPES = {
    "activity",
    "monitoring_b",
    49,  # sleep (proprietary, no profile name)
    68,  # HRV (proprietary, no profile name)
}

def field_types_for(mesg_num):
    """Return {field name: profile type} for one message number."""
    field_types = {}

    for field in Profile["messages"][mesg_num]["fields"].values():
        field_types[field["name"]] = field["type"]

        for sub_field in field["sub_fields"]:
            field_types[sub_field["name"]] = sub_field["type"]

    return field_types

def file_to_rows(path, export_sha256, loaded_at):
    """Return {table_name: [row, row, ...]} for one FIT file."""
    messages_in_order = []

    def collect_message(mesg_num, message):
        messages_in_order.append((len(messages_in_order), mesg_num, message))

    stream = Stream.from_file(path)
    decoder = Decoder(stream)

    messages, errors = decoder.read(
        apply_scale_and_offset = True,
        convert_datetimes_to_dates = True,
        convert_types_to_strings = True,
        expand_sub_fields = True,
        expand_components = False,
        merge_heart_rates = False,
        mesg_listener  = collect_message
    )

    rows = defaultdict(list)

        
    file_type = messages["file_id_mesgs"][0]["type"]

    if file_type not in RETAINED_FILE_TYPES:
        return rows

    for index, mesg_num, message in messages_in_order:

        if mesg_num not in Profile["messages"]:
            continue

        table_name = Profile["messages"][mesg_num]["name"]

        if table_name not in BRONZE_FIT_TABLES:
            continue

        field_types = field_types_for(mesg_num)
        defined_fields = {}

        for field_name, value in message.items():
            if isinstance(field_name,str) and field_name != "developer_fields":
                field_type = field_types.get(field_name)

                if field_type in Profile["types"] and field_type not in NUMERIC_PROFILE_TYPES and isinstance(value,int):
                    defined_fields[field_name] = str(value)
                else:
                    defined_fields[field_name] = value

        row = {
            **defined_fields,
            "_source_path": str(path.relative_to("data/raw")),
            "_file_type": str(file_type),
            "_message_index": index,
            "_loaded_at": loaded_at,
            "_export_sha256": export_sha256
        }
        rows[table_name].append(row)
    
    return rows

if __name__ == "__main__":
    path = Path(sys.argv[1])
    rows = file_to_rows(path, export_sha256="test", loaded_at=datetime.now(timezone.utc))

    for table, table_rows in sorted(rows.items()):
        print(table, len(table_rows))
    
    for table, table_rows in sorted(rows.items()):
        print(table, sorted(table_rows[0].keys()))

    print(field_types_for(0))