import json
import requests
import re
import time

#Gets the the changed code lines from github and also the  absolute path of the files

input_json = r"FuzzabilityAnalysisOfDeepBugs\Data\github_commit_links_with_dates.json"
output_json = r"FuzzabilityAnalysisOfDeepBugs\Data\commit_lines_output_withDates_withFullPath.json"
sleep_seconds = 0.90

# --- REGEX ---
COMMIT_RE = re.compile(r"https://github\.com/([^/]+/[^/]+)/commit/([a-f0-9]{6,40})")

# --- Load input ---
with open(input_json, "r", encoding="utf-8") as f:
    data = json.load(f)

results = []
i = 0
for entry in data:
    file_name = entry.get("file")
    project = entry.get("project")
    published_date = entry.get("published")
    commit_links = entry.get("commit_links", [])
    i += 1
    print(f"current entry {file_name} {i}")
    commit_results = []

    for commit_url in commit_links:
        m = COMMIT_RE.match(commit_url)
        if not m:
            print(f"⚠️ Skipping invalid commit URL: {commit_url}")
            continue

        repo = m.group(1)
        commit_hash = m.group(2)
        patch_url = commit_url + ".patch"

        try:
            resp = requests.get(patch_url, timeout=30)
            if resp.status_code != 200:
                print(f"❌ Failed to fetch {patch_url}: HTTP {resp.status_code}")
                continue
            patch_text = resp.text
        except Exception as e:
            print(f"❌ Exception fetching {patch_url}: {e}")
            continue

        # --- Parse patch ---
        files = {}
        current_file = None
        old_line_num = None
        new_line_num = None

        for line in patch_text.splitlines():
            if line.startswith("diff --git"):
                # ✅ Strict regex to extract full path after b/
                match = re.match(r"diff --git a/(.+?) b/(.+)", line)
                if match:
                    current_file = match.group(2)  # full path relative to repo
                    files[current_file] = {"added": [], "removed": []}
                old_line_num = None
                new_line_num = None
                continue

            if not current_file:
                continue

            header_match = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
            if header_match:
                old_line_num = int(header_match.group(1))
                new_line_num = int(header_match.group(3))
                continue

            if line.startswith("---") or line.startswith("+++") or line.startswith("index") or not line.strip():
                continue

            if line.startswith("+"):
                if new_line_num is not None:
                    files[current_file]["added"].append(new_line_num)
                    new_line_num += 1
                continue

            if line.startswith("-"):
                if old_line_num is not None:
                    files[current_file]["removed"].append(old_line_num)
                    old_line_num += 1
                continue

            # context line
            if old_line_num is not None:
                old_line_num += 1
            if new_line_num is not None:
                new_line_num += 1

        commit_results.append({
            "commit_url": commit_url,
            "repo": repo,
            "commit_hash": commit_hash,
            "files_changed": files
        })

        time.sleep(sleep_seconds)

    results.append({
        "file": file_name,
        "project": project,
        "published": published_date,
        "commit_changes": commit_results
    })

# --- Save output ---
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"✅ Done! Results saved to {output_json}")