import os
import json

# This script filters OSV entries based on whether they are associated with OSS-Fuzz projects.
# It reads OSV JSON files, checks the 'affected' field for package names, and categorizes 
# them into 'InFuzz' or 'NotInFuzz' directories based on a JSON including all OSS-Fuzz projects.
input_Path = r'Data\OSV'
inOss_Path = r'Data\Filtered1\InFuzz'
noOss_Path = r'Data\Filtered1\NotInFuzz'

oss_filter_path = r'Data\OSS_Fuzz_projects.json'


os.makedirs(inOss_Path, exist_ok=True)
os.makedirs(noOss_Path, exist_ok=True)

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
    
    if IsInOSS_Fuzz:
        # uses whatever 'package_name' was extracted during the loop
        data['OSS_Project'] = package_name

    target_path = inOss_Path if IsInOSS_Fuzz else noOss_Path

    with open(os.path.join(target_path, osv_name), 'w') as f:
        json.dump(data, f)

    if i % 100 == 0:
        print(f'Processed {i} files...')