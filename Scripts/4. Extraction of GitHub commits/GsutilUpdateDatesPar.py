import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# messed up while installing gsutil and was lazy, should find it in PATH or common install locations
input_file = r'Data\commit_lines_output_withDates_GitHub_updated.json'
output_file = r'Data\commit_lines_output_withDates_GitHub_updated_GsutilUpdated.json'
def get_gsutil_path():
    path = shutil.which("gsutil")
    if path:
        return path

    possible_paths = [
        Path.home() / "google-cloud-sdk" / "bin" / "gsutil.cmd",
        Path(os.getenv("LOCALAPPDATA", "")) / "Google" / "Cloud SDK" / "google-cloud-sdk" / "bin" / "gsutil.cmd",
        Path(os.getenv("PROGRAMFILES", "")) / "Google" / "Cloud SDK" / "google-cloud-sdk" / "bin" / "gsutil.cmd",
        Path(os.getenv("PROGRAMFILES(X86)", "")) / "Google" / "Cloud SDK" / "google-cloud-sdk" / "bin" / "gsutil.cmd",
    ]
    for p in possible_paths:
        if p.exists():
            return str(p)
    return None

# Get report folders 
def get_report_folders(gsutil_path, project):
    """Return a sorted list of report folders for a given project."""
    bucket_path = f"gs://oss-fuzz-coverage/{project}/reports/"
    try:
        result = subprocess.run(
            [gsutil_path, "ls", bucket_path],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        folders = [
            os.path.basename(line.strip("/"))
            for line in result.stdout.splitlines()
            if line.strip().endswith("/")
        ]
        folders = [f for f in folders if f.isdigit() and len(f) == 8]
        return sorted(folders)
    except subprocess.TimeoutExpired:
        print(f"⚠️ Timeout fetching {project}")
        return []
    except Exception as e:
        print(f"⚠️ Error fetching {project}: {e}")
        return []

#  Adjust published date 
def adjust_published_date(entry, available_dates):
    """If the published date folder doesn't exist, set to closest earlier folder."""
    if not available_dates:
        return entry

    pub_date = datetime.strptime(entry["published"][:10], "%Y-%m-%d")
    pub_ymd = pub_date.strftime("%Y%m%d")

    if pub_ymd in available_dates:
        return entry

    earlier = [d for d in available_dates if d <= pub_ymd]
    if earlier:
        new_folder = earlier[-1]
        entry["published"] = datetime.strptime(new_folder, "%Y%m%d").strftime("%Y-%m-%dT%H:%M:%SZ")
    return entry

#  Worker 
def process_project(entry, gsutil_path):
    project = entry.get("project")
    if not project:
        return entry
    folders = get_report_folders(gsutil_path, project)
    return adjust_published_date(entry, folders)

#  Main workflow 
def process_json(input_json, output_file, max_workers=8):
    gsutil_path = get_gsutil_path()
    if not gsutil_path:
        print("⚠️ gsutil not found! Please check your Google Cloud SDK installation.")
        return

    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    updated = []

    print(f"🚀 Starting processing of {total} projects...\n")

    # Run gsutil calls concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {executor.submit(process_project, entry, gsutil_path): entry for entry in data}
        done_count = 0
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            project = entry.get("project", "unknown")
            try:
                result = future.result()
                updated.append(result)
            except Exception as e:
                print(f"⚠️ Error processing {project}: {e}")
                continue

            done_count += 1
            print(f"✅ [{done_count}/{total}] Processed {project}")

    # Save updated JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=4)

    print(f"\n All done! {done_count}/{total} projects processed successfully.")
    print(f"📄 Updated JSON saved to: {output_file}")

#  Run 
if __name__ == "__main__":
    process_json(input_file, output_file)