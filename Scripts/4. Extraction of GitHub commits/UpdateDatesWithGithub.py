import json
import requests
from datetime import datetime, timedelta
import time


#Fix published tag if the github commit change date is different 

input_json = r"Data\commit_lines_output_withDates_withFullPath.json"
output_json = r"Data\commit_lines_output_withDates_GitHub_updated.json"
sleep_seconds = 0.5  #  delay to avoid rate limits
github_token = "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"  # replace with your GitHub token 

headers = {}
if github_token:
    headers["Authorization"] = f"token {github_token}"

# --- Load input JSON ---
with open(input_json, "r", encoding="utf-8") as f:
    data = json.load(f)

for entry in data:
    published_str = entry.get("published")
    if not published_str:
        continue

    # start with the existing published date
    original_published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
    earliest_commit_date = None

    for commit in entry.get("commit_changes", []):
        commit_url = commit.get("commit_url")
        if not commit_url:
            continue

        parts = commit_url.rstrip("/").split("/")
        if len(parts) < 7:
            print(f"⚠️ Invalid commit URL: {commit_url}")
            continue

        owner, repo, commit_hash = parts[3], parts[4], parts[6]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_hash}"

        try:
            resp = requests.get(api_url, headers=headers, timeout=20)
            if resp.status_code != 200:
                print(f" Failed to fetch {api_url}: {resp.status_code}")
                continue

            commit_data = resp.json()
            commit_date_str = commit_data["commit"]["committer"]["date"]
            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))

            # Track earliest commit date
            if earliest_commit_date is None or commit_date < earliest_commit_date:
                earliest_commit_date = commit_date

        except Exception as e:
            print(f" Exception fetching {api_url}: {e}")
            continue

        time.sleep(sleep_seconds)

    if earliest_commit_date:
        new_published = earliest_commit_date
        entry["published"] = new_published.isoformat().replace("+00:00", "Z")
        print(f"📅 {entry['file']}: updated published to {entry['published']}")

# --- Save updated JSON ---
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

print(f"✅ Done! Updated JSON saved to {output_json}")