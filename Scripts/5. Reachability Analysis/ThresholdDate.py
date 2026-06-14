import json
import os
from datetime import datetime

#Scrips Thresholds the dates by comparing their remidation date with coverage report dates, and keeps only those where the difference is under 30 days

json_a_path = r"Data\commit_lines_output_withDates_GitHub_updated.json"
json_b_path = r"Data\coverage_hits_ordered.json"
output_filtered_path = r"Data\coverage_hits_ordered_under30.json"

threshold_days = 30

def parse_date(date_str):
    """Convert ISO date to datetime, return None if invalid."""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return None


#  LOAD JSONS 
with open(json_a_path, "r", encoding="utf-8") as f:
    json_a = json.load(f)

with open(json_b_path, "r", encoding="utf-8") as f:
    json_b = json.load(f)

# Build lookup: source → published date in JSON A
a_lookup = {entry["file"]: entry.get("published") for entry in json_a}

# Store filtered B entries
filtered_entries = []

# PROCESS B STRUCTURE 
for entry in json_b:

    source_name = entry.get("source")
    b_file = entry["files"][0]   # one file per entry
    b_pub_str = b_file.get("published", "")
    b_pub = parse_date(b_pub_str)

    # Lookup published date in JSON A (A uses "file")
    a_pub_str = a_lookup.get(source_name)
    a_pub = parse_date(a_pub_str) if a_pub_str else None

    if not a_pub or not b_pub:
        continue  # skip invalid or missing dates

    diff_days = (a_pub - b_pub).days

    if abs(diff_days) <= threshold_days:
        # Keep this entry **unchanged**, but attach the diff for sorting
        filtered_entries.append({
            "source": source_name,
            "files": entry["files"],
            "_difference_days": diff_days  # temporary for sorting
        })

#  SORT by difference_days 
filtered_entries.sort(key=lambda x: x["_difference_days"])

# Remove temporary field before output
for e in filtered_entries:
    del e["_difference_days"]

#  SAVE RESULT 
with open(output_filtered_path, "w", encoding="utf-8") as out:
    json.dump(filtered_entries, out, indent=4)

print(f"📄 Saved CoveredOrdered-style <30-day entries to:\n{output_filtered_path}")
