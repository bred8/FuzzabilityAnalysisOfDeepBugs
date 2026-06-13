import os
import json

#script simply puts all the OSS_Fuzz Projects into a JSON file

input_Path = r'FuzzabilityAnalysisOfDeepBugs\Data\OSS-Fuzz\oss-fuzz\projects' #add path with all the OSS-Fuzz project folders
destination = r'FuzzabilityAnalysisOfDeepBugs\Data\OSS_Fuzz_projects.json'

projects = []
for oss_name in os.listdir(input_Path):
    projects.append(oss_name)
    with open(destination,'w') as f:
        json.dump(projects,f)