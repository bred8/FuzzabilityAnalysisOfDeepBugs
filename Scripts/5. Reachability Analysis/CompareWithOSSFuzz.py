import os
import json
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# Script compares removed lines with coverage reports to find hits where removed lines were covered by OSS-Fuzz.

input_file = r"Data\commit_lines_output_withDates_GitHub_updated_GsutilUpdated.json"
output_hits = r"Data\coverage_hits.json"
MAX_WORKERS = 15   
TIMEOUT = 20       # seconds for requests

#  Load input data 
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

#  Build coverage check tasks 
tasks = []
for entry in data:
    project = entry.get("project", "")
    file_name = entry.get("file", "")
    published = entry.get("published", "")

    if not project or not published:
        continue

    try:
        date_str = datetime.fromisoformat(published.replace("Z", "")).strftime("%Y%m%d")
    except ValueError:
        print(f"⚠️ Invalid date format in {file_name}: {published}")
        continue

    for commit in entry.get("commit_changes", []):
        commit_url = commit.get("commit_url")
        for changed_file, changes in commit.get("files_changed", {}).items():
            removed = changes.get("removed", [])
            if not removed:
                continue  # only check files that had removed lines

            # Two possible base paths for coverage reports
            urls = [
                f"https://storage.googleapis.com/oss-fuzz-coverage/"
                f"{project}/reports/{date_str}/linux/src/{project}/{changed_file}.html",

                f"https://storage.googleapis.com/oss-fuzz-coverage/"
                f"{project}/reports/{date_str}/linux/proc/self/cwd/{changed_file}.html",

                f"https://storage.googleapis.com/oss-fuzz-coverage/"
                f"{project}/reports/{date_str}/linux/{changed_file}.html",

                f"https://storage.googleapis.com/oss-fuzz-coverage/"
                f"{project}/reports/{date_str}/linux/src/{changed_file}.html",

                f"https://storage.googleapis.com/oss-fuzz-coverage/"
                f"{project}/reports/{date_str}/linux/work/{project}/{changed_file}.html",

                f"https://storage.googleapis.com/oss-fuzz-coverage/"
                f"{project}/reports/{date_str}/linux/{project}/{changed_file}.html",

                f"https://storage.googleapis.com/oss-fuzz-coverage/"
                f"{project}/reports/{date_str}/linux/src/out/{project}/{changed_file}.html",
                ]
            
            tasks.append({
                "project": project,
                "file": changed_file,
                "urls": urls,
                "source_json": file_name,
                "commit_url": commit_url,
                "published": published,
                "removed": removed,
            })

print(f"📦 Created {len(tasks)} coverage check tasks.\n")

#  Worker function 
def check_coverage(task):
    removed_lines = task.get("removed", [])
    urls = task["urls"]

    result = {
        "project": task["project"],
        "file": task["file"],
        "removed_lines": removed_lines,
        "covered_removed_lines": [],
        "source_json": task["source_json"],
        "commit_url": task["commit_url"],
        "published": task["published"],
        "url": None,
    }

    for url in urls:
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue  # try the next URL pattern

            soup = BeautifulSoup(resp.text, "html.parser")
            covered_lines = set()

            for tr in soup.find_all("tr"):
                line_no_tag = tr.find("td", class_="line-number")
                if not line_no_tag:
                    continue
                try:
                    line_no = int(line_no_tag.get_text(strip=True))
                except ValueError:
                    continue
                if tr.find("td", class_="covered-line"):
                    covered_lines.add(line_no)

            for ln in removed_lines:
                if ln in covered_lines:
                    result["covered_removed_lines"].append(ln)

            # Keep only if at least one removed line was covered
            if result["covered_removed_lines"]:
                result["url"] = url
                return result

        except Exception:
            continue  # if network error, try next URL

    return None  # none of the URLs had coverage for removed lines

#  Run all tasks in parallel 
hits = []

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(check_coverage, task): task for task in tasks}

    for i, future in enumerate(as_completed(futures), 1):
        try:
            res = future.result()
            if res:
                hits.append(res)
                print(f"✅ [{i}/{len(tasks)}] Covered removed lines found in: {res['url']}")
            else:
                print(f"❌ [{i}/{len(tasks)}] No coverage for removed lines.")
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")

#  Save results (only hits) 
with open(output_hits, "w", encoding="utf-8") as f:
    json.dump(hits, f, indent=4)

print("\n✅ Finished.")
print(f"   ✅ {len(hits)} files had covered removed lines → saved to {output_hits}")