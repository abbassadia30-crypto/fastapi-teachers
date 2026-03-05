import json

def extract_student_directory(db_json):
    sections = db_json.get("sections", {})
    directory = []

    for section_name, content in sections.items():
        # content contains 'students', 'results', 'attendance'
        for s in content.get("students", []):
            directory.append({
                "n": s.get("name"),
                "fn": s.get("father_name"),
                "c": s.get("extra_fields", {}).get("Phone", "N/A"),
                "s": section_name # Taking section name from the key
            })
    return directory

def get_global_counts(db_json):
    sections_data = db_json.get("sections", {})
    total_sections = len(sections_data.keys())
    total_students = 0
    for section in sections_data.values():
        total_students += len(section.get("students", []))

    return {
        "total_sections": total_sections,
        "total_students": total_students,
        "section_names": list(sections_data.keys())
    }

def extract_global_marks(db_json):
    sections = db_json.get("sections", {})
    all_marks = []

    for section_name, content in sections.items():
        results = content.get("results", [])
        for res in results:
            m_data = res.get("marks_data", {})

            # Handle if marks_data is a list or a single dictionary
            marks_list = m_data if isinstance(m_data, list) else [m_data]

            for entry in marks_list:
                try:
                    obt = float(entry.get("obt", 0))
                    max_m = float(entry.get("max", 0))
                except (ValueError, TypeError):
                    obt, max_m = 0.0, 0.0

                all_marks.append({
                    "n": res.get("student_name"),
                    "fn": res.get("father_name"),
                    "s": section_name,
                    "exam": res.get("exam_title"),
                    "sub": entry.get("subject"),
                    "om": obt,
                    "tm": max_m
                })
    return all_marks

def get_attendance_pulse(db_json):
    sections = db_json.get("sections", {})
    pulse = {}

    for section_name, content in sections.items():
        logs = content.get("attendance", [])
        for log in logs:
            date = log.get("log_date") # e.g., "2026-03-01"
            if date not in pulse:
                pulse[date] = {"p": 0, "a": 0}

            pulse[date]["p"] += log.get("p_count", 0)
            pulse[date]["a"] += log.get("a_count", 0)

    # Sort latest dates first
    sorted_pulse = dict(sorted(pulse.items(), reverse=True)[:3])
    return sorted_pulse
