import os
import json
from git import Repo


# This script retrieves the creation dates of all OSS-Fuzz projects by analyzing the Git commit history of the OSS-Fuzz repository.
# Define paths and output file name
repo_path = r"Data\OSS-Fuzz\oss-fuzz"  
output_file = r"Data\projects_dates.json"
projects_dir_path = os.path.join(repo_path, "projects")

project_dates = {}

# Initialize the Git repository
try:
    repo = Repo(repo_path)
except Exception as e:
    print(f"❌ Error: Could not initialize repository at {repo_path}: {e}")
    exit(1)

# Verify the projects directory exists before proceeding
if not os.path.exists(projects_dir_path):
    print(f"❌ Error: 'projects' directory not found at {projects_dir_path}")
    exit(1)

# Collect and sort all subdirectories within the projects folder
projects = [d for d in os.listdir(projects_dir_path) if os.path.isdir(os.path.join(projects_dir_path, d))]

for project in sorted(projects):
    print(f"Checking {project}...")

    try:
        # FORCE forward slashes so Git internal engine stays happy on Windows
        project_rel_path = f"projects/{project}"

        # Get all commits that touched this project directory
        commits = list(repo.iter_commits(paths=project_rel_path))
        
        if commits:
            # Git lists commits from NEWEST to OLDEST.
            # Therefore, the very LAST element [-1] is the day the folder was created.
            first_commit = commits[-1]
            date_str = first_commit.authored_datetime.isoformat()
            
            print(f"  📅 Added on: {date_str}")
            project_dates[project] = date_str
        else:
            print("  ❌ Could not find date")
            project_dates[project] = None

    except Exception as e:
        print(f"  ⚠️ Error processing {project}: {e}")
        project_dates[project] = None

# Ensure the Data parent folder exists before writing to it
output_dir = os.path.dirname(output_file)
if output_dir:
    os.makedirs(output_dir, exist_ok=True)

# Write the final mapping to a formatted JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(project_dates, f, indent=4)

print(f"\n✅ All results saved in {output_file}")