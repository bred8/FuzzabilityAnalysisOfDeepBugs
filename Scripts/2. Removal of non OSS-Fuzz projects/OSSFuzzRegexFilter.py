import os
import json
import re

#Alpha version of regex dont use this, use OSSFuzzRegexFilterBetter.py

input_Path = r'FuzzabilityAnalysisOfDeepBugs\Data\OSV'
Tag_Path = r'' 
no_Tag_Path = r'' 
oss_filter_path = r'' 


with open(oss_filter_path, 'r') as filter_file:
    oss_filter = {p.lower() for p in json.load(filter_file)}

# Pre-compile regex patterns once with optional plural/  genetive 's'
patterns = [(project, re.compile(r'\b' + re.escape(project) + r's?\b')) for project in oss_filter]

i = 0
with os.scandir(input_Path) as entries:
    for entry in entries:
        if not entry.name.endswith('.json') or not entry.is_file():
            continue

        try:
            with open(entry.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to read {entry.name}: {e}")
            continue

        is_in_oss = False
        matched_project = None

        for field in ['details', 'summary']:
            if field in data and isinstance(data[field], str):
                content = data[field].lower()
                for project, pattern in patterns:
                    if pattern.search(content):
                        is_in_oss = True
                        matched_project = project
                        break
            if is_in_oss:
                break

        out_dir = Tag_Path if is_in_oss else no_Tag_Path

        if is_in_oss:
            data['OSS_Project'] = matched_project

        output_file = os.path.join(out_dir, entry.name)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        i += 1
        if i % 100 == 0:
            print(f"✅ Processed {i} files...")