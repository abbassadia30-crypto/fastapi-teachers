import json

def extract_section_directory(section_content, section_name):
    """
    This function expects ONLY the dictionary inside '10th-A'
    """
    students = section_content.get("students", [])
    return [
        {
            "n": s.get("name"),
            "fn": s.get("father_name"),
            "c": s.get("extra_fields", {}).get("Phone", "N/A"),
            "s": section_name
        }
        for s in students
    ]

# YOUR DATA
data_from_db = {
    "sections": {
        "10th-A": {
            "students": [
                {"id": 1, "name": "Ali Hassan", "father_name": "Abbas Ali", "section": "10th-A", "extra_fields": {}},
                {"id": 4, "name": "Asad", "father_name": "Shahzad", "section": "10th-A", "extra_fields": {"Phone": "034017012244"}}
            ]
        }
    }
}

# --- THE FIX ---
# You must drill down into the section first!
section_to_calculate = "10th-A"
target_data = data_from_db["sections"][section_to_calculate]

# Now call it with the Targeted Section Data
result = extract_section_directory(target_data, section_to_calculate)

# Print it so you can see the result in the terminal
print(json.dumps(result, indent=2))