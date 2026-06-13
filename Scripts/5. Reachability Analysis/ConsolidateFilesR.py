import json

input_file = r'FuzzabilityAnalysisOfDeepBugs\Data\coverage_hits.json'
output_file = r'FuzzabilityAnalysisOfDeepBugs\Data\coverage_hits_ordered.json'

def restructure_json(data):
    # Initialize the result dictionary
    result = {}

    # Process each entry in the input data
    for entry in data:
        # Extract the source_json key without the .json extension
        source = entry['source_json'].replace('.json', '')

        # Ensure the source exists in the result dictionary
        if source not in result:
            result[source] = {
                "project": entry["project"],
                "file_entries": []
            }
        
        # Append the current entry's file data to the file_entries list
        result[source]["file_entries"].append({
            "file": entry["file"],
            "removed_lines": entry["removed_lines"],
            "covered_removed_lines": entry["covered_removed_lines"],
            "commit_url": entry["commit_url"],
            "published": entry["published"],
            "url": entry["url"]
        })

    return result

# Input file path

# Read the input file
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Call the restructure function
output = restructure_json(data)

# Save the output to a new JSON file using json.dump
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=4)  # Directly dump the result

print("Restructured JSON has been saved to:", output_file)