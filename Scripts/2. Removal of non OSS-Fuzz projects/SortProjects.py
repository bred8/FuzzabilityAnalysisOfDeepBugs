import os
import json


oss_filter_path = r'Data\OSS_Fuzz_projects.json'

with open(oss_filter_path,'r') as f:
    projects = json.load(f)

projects = sorted(projects,key=lambda x: len(x))
projects.reverse()
#print(projects)

with open(r'Data\sorted_Projects.json','w+') as f:
    json.dump(projects,f)