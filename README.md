# Thesis Repository: Fuzzability analysis of deep bugs

This repository contains the datasets, scripts, and some intermediary data used during the writing of my thesis.

## Prerequisites and Dependencies
* **Python:** `3.10.6`
* **Google Cloud SDK:** `gsutil` version `5.34` (local installation required)
* **Python Packages:** Install via `pip install -r requirements.txt`

## Data Structure Setup
Before running the scripts, you must set up the local data directories as follows:

* `Data\OSV\` - Needs the raw JSON files downloaded from the OSV dataset.
* `Data\OSS-Fuzz\` - Needs a clone of the `oss-fuzz` repository structured like this:
  `Data\OSS-Fuzz\oss-fuzz\...`

> **Note on Large Files:** The `UsedData` directory contains the relevant JSONs used in the final thesis. However, the full datasets and some larger intermediary JSON files were too large to push to GitHub. They are available upon request.

## Configuration and GitHub Access Tokens
You must generate your own **GitHub Personal Access Token** and add it to the following script files before execution:
1. `Scripts\4. Extraction of GitHub commits\UpdateDatesWithGithub.py`
2. `Scripts\6. Removal of fuzzed entries\RecheckGithubPar.py`

