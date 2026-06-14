import os
import json
import re

# This script filters OSV entries based on regex matching of OSS-Fuzz project names in the 'details' and 'summary' fields.
# removes very highly error prone projects

input_Path = r'Data\OSV'
Tag_Path = r'Data\Filtered2\RegexBetter\hasTag'
no_Tag_Path = r'Data\Filtered2\RegexBetter\noTag'
oss_filter_path = r'Data\sorted_Projects.json'
removed_projects = ['file','firefox','requests', 'time', 'php','xs','example','json',]

os.makedirs(Tag_Path, exist_ok=True)
os.makedirs(no_Tag_Path, exist_ok=True)

with open(oss_filter_path, 'r') as filter_file:
    oss_filter = {p.lower() for p in json.load(filter_file)}
    oss_filter = [x for x in oss_filter if x not in removed_projects]

# Pattern full word only, and plural allowed
patterns = [(project, re.compile(r'\b' + re.escape(project) + r's?\b')) for project in oss_filter]

# Create main directories if they don't exist
os.makedirs(Tag_Path, exist_ok=True)
os.makedirs(no_Tag_Path, exist_ok=True)

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
        
        if is_in_oss:
            # CHANGED: Dropped the subfolder creation. 
            # Files are now saved directly to the root of Tag_Path.
            out_dir = Tag_Path
            data['OSS_Project'] = matched_project
        else:
            out_dir = no_Tag_Path
        
        output_file = os.path.join(out_dir, entry.name)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        i += 1
        if i % 100 == 0:
            print(f"✅ Processed {i} files...")

print(f"Completed processing {i} files!")
print(f"Files with OSS projects organized in: {Tag_Path}")
print(f"Files without OSS projects in: {no_Tag_Path}")