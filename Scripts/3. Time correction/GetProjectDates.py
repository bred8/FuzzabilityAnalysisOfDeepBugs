import os
import json
from git import Repo

# Define paths and output file name
repo_path = r"FuzzabilityAnalysisOfDeepBugs\Data\OSS-Fuzz\oss-fuzz"  # Path to the local clone of the OSS-Fuzz repository might need to be changed
output_file = r"FuzzabilityAnalysisOfDeepBugs\Data\projects_dates.json"
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
    # Construct the relative path to the project for Git querying
    project_rel_path = os.path.join("projects", project)
    print(f"Checking {project}...")

    try:
        # Search for commits where this path was first added ('A')
        # follow=True ensures we track the history across potential renames
        commits = list(repo.iter_commits(paths=project_rel_path, diff_filter='A', follow=True))
        
        if commits:
            # The oldest commit (first addition) is the last element in the list
            first_commit = commits[-1]
            # Format the date to ISO 8601 string
            date_str = first_commit.authored_datetime.isoformat()
            
            print(f"  📅 Added on: {date_str}")
            project_dates[project] = date_str
        else:
            # Handle cases where no explicit 'Added' commit is found in history
            print("  ❌ Could not find date")
            project_dates[project] = None

    except Exception as e:
        print(f"  ⚠️ Error processing {project}: {e}")
        project_dates[project] = None

# Write the final mapping to a formatted JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(project_dates, f, indent=4)

print(f"\n✅ All results saved in {output_file}")