import os
import json
import re




#Extracts all the github links from 
input_folder = r"Data\MergedFixedDates"
output_file = r"Data\github_commit_links_with_dates.json"

#  match GitHub commit URLs 
COMMIT_RE = re.compile(
    r"https://github\.com/[\w\.-]+/[\w\.-]+/commit/[a-f0-9]{6,40}",
    re.IGNORECASE
)

# Helper: recursively extract all strings ---
def extract_strings(obj):
    """Recursively extract all string values from a nested JSON structure."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from extract_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from extract_strings(v)
    elif isinstance(obj, str):
        yield obj

# main processing loop
results = []

for root, _, files in os.walk(input_folder):
    for filename in files:
        if not filename.endswith(".json"):
            continue
        
        full_path = os.path.join(root, filename)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to read {filename}: {e}")
            continue

        project = data.get("OSS_Project", "")
        published_date = data.get("published", None)
        commit_links = set()

        # Extract commit links from all string fields
        for text in extract_strings(data):
            for match in COMMIT_RE.findall(text):
                commit_links.add(match)

        if commit_links:
            results.append({
                "file": filename,
                "project": project,
                "published": published_date,
                "commit_links": list(commit_links)
            })

print(f"✅ Found {len(results)} JSON files with GitHub commit links")

# --- Save to file ---
with open(output_file, "w", encoding="utf-8") as out:
    json.dump(results, out, indent=4)

print(f"📄 Results saved to {output_file}")