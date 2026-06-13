import os
import json


input_Path = r'FuzzabilityAnalysisOfDeepBugs\Data\OSV'
inOss_Path = r'FuzzabilityAnalysisOfDeepBugs\Data\Filtered1\NotInFuzz'
noOss_Path = r'FuzzabilityAnalysisOfDeepBugs\Data\OSV\Filtered1\InFuzz'

oss_filter_path = r'FuzzabilityAnalysisOfDeepBugs\Data\OSS_Fuzz_projects.json'

# Load OSS-Fuzz filter list once
with open(oss_filter_path, 'r') as filter_file:
    oss_filter = json.load(filter_file)

i = 0

for osv_name in os.listdir(input_Path):
    i += 1

    with open(os.path.join(input_Path, osv_name), 'r') as osv_json:
        data = json.load(osv_json)

    affected = data.get('affected', [])

    IsInOSS_Fuzz = False

    if isinstance(affected, list):
        for entry in affected:
            if isinstance(entry, dict) and 'package' in entry:
                package_name = entry['package'].get('name')
                if package_name and package_name in oss_filter:
                    IsInOSS_Fuzz = True
                    break
    elif isinstance(affected, dict):
        package_name = affected.get('package', {}).get('name')
        if package_name and package_name in oss_filter:
            IsInOSS_Fuzz = True

    target_path = inOss_Path if IsInOSS_Fuzz else noOss_Path

    with open(os.path.join(target_path, osv_name), 'w') as f:
        json.dump(data, f)

    if i % 100 == 0:
        print(f'Processed {i} files...')