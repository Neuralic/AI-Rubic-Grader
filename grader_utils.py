import json
import os

RESULTS_FILE = "grading_results.json"

def write_result_to_file(result):
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(result)

    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def read_all_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []