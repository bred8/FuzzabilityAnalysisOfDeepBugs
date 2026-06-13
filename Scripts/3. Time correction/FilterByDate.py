import os
import json
from datetime import datetime

# Paths
json_folder = r"FuzzabilityAnalysisOfDeepBugs\Data\MergedDataset"              # Folder with advisories
projects_dates_file = r"FuzzabilityAnalysisOfDeepBugs\Data\projects_dates.json"  # Project → date added to OSS-Fuzz
output_root = r"FuzzabilityAnalysisOfDeepBugs\Data\MergedFixedDates"               # Root folder for filtered dataset

# Load project add dates
with open(projects_dates_file, 'r', encoding='utf-8') as f:
    projects_dates = json.load(f)

processed_count = 0
kept_count = 0

for filename in os.listdir(json_folder):
    if not filename.endswith(".json"):
        continue
    
    file_path = os.path.join(json_folder, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON: {filename}")
            continue

    oss_project = data.get("OSS_Project")
    published_str = data.get("published")  # e.g., "2020-12-15T16:03:21Z"

    if not oss_project or not published_str:
        continue  # Skip if missing necessary info

    project_added_str = projects_dates.get(oss_project)
    if not project_added_str:
        continue  # Skip if project not in OSS-Fuzz

    # Parse dates
    published_date = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
    project_added_date = datetime.fromisoformat(project_added_str.replace("Z", "+00:00"))

    # Keep only advisories published on/after project was added
    if published_date >= project_added_date:
        # Create project subfolder
        project_folder = os.path.join(output_root, oss_project)
        os.makedirs(project_folder, exist_ok=True)

        # Save JSON in the project subfolder
        out_path = os.path.join(project_folder, filename)
        with open(out_path, 'w', encoding='utf-8') as out_f:
            json.dump(data, out_f, indent=2)

        kept_count += 1

    processed_count += 1
    if processed_count % 100 == 0:
        print(f"Processed {processed_count} files, kept {kept_count} so far...")

print(f"✅ Finished processing {processed_count} files. Total kept: {kept_count}")