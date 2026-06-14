import json

#restructures JSON from a flat list of files to a nested structure grouped by entry, with files under each source.

input_file = r"Data\coverage_hits.json"
output_file = r"Data\coverage_hits_ordered.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

merged = {}

for entry in data:
    src = entry["source_json"]

    if src not in merged:
        merged[src] = {
            "source": src,
            "files": []
        }

    # Copy file-level data but remove the key "source_json"
    file_info = {
        key: value
        for key, value in entry.items()
        if key != "source_json"
    }

    merged[src]["files"].append(file_info)

# Convert dict to list
output_list = list(merged.values())

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_list, f, indent=4)

print(f"✔️ Merged {len(data)} entries into {len(output_list)} grouped items.")