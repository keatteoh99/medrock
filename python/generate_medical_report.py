from datetime import datetime

def generate_medical_report(patient_info, symptoms, possible_conditions, urgency_level):
    """
    Generate a structured medical report for MedRock.

    Parameters:
    - patient_info: dict with keys 'name', 'age', 'gender', 'medical_history' (list or string)
    - symptoms: list of dicts, each with 'name', optional 'severity', 'duration'
    - possible_conditions: list of strings (preliminary considerations)
    - urgency_level: string, e.g., 'Green', 'Orange', 'Red'
    """
    report_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Format patient summary
    medical_history = patient_info.get("medical_history", [])
    if isinstance(medical_history, list):
        medical_history_str = ", ".join(medical_history)
    else:
        medical_history_str = str(medical_history)

    # Format symptoms
    symptom_lines = []
    for s in symptoms:
        line = f"- {s['name']}"
        if 'severity' in s:
            line += f" – {s['severity']}"
        if 'duration' in s:
            line += f", {s['duration']}"
        if 'onset_date' in s:
            line += f", onset: {s['onset_date']}"
        symptom_lines.append(line)
    
    # Format possible conditions
    conditions_str = "\n".join([f"- {c}" for c in possible_conditions])

    # Recommended actions based on urgency
    actions = []
    if urgency_level.lower() == 'red':
        actions = [
            "Call your local emergency services or go to the nearest emergency department immediately",
            "Bring current medications and medical history for assessment",
            "Avoid strenuous activity until evaluated by a licensed healthcare professional"
        ]
    elif urgency_level.lower() == 'orange':
        actions = [
            "Schedule a clinic appointment soon",
            "Monitor symptoms and seek medical care if they worsen"
        ]
    else:  # Green / mild
        actions = [
            "Monitor symptoms at home",
            "Consult a healthcare provider if symptoms persist or worsen"
        ]
    actions_str = "\n".join([f"- {a}" for a in actions])

    # Build full report
    report = f"""
=== Medical Report ===
Report generated: {report_time}

Patient Summary:
- Patient ID: {patient_info.get('patient_id', 'N/A')}
- Name: {patient_info.get('name', 'N/A')}
- Age: {patient_info.get('age', 'N/A')}
- Gender: {patient_info.get('gender', 'N/A')}
- Medical History: {medical_history_str}

Symptoms:
{chr(10).join(symptom_lines)}

Possible Conditions (Preliminary):
{conditions_str}

Urgency Level: {urgency_level.upper()} – {'HIGH ⚠️' if urgency_level.lower()=='red' else 'Moderate' if urgency_level.lower()=='orange' else 'Low'}
{'Immediate medical attention is strongly recommended.' if urgency_level.lower()=='red' else ''}

Recommended Actions:
{actions_str}

Disclaimer:
This report is based on the information provided by the patient and is not a substitute for professional medical evaluation. A licensed medical professional should confirm and act on this information.
"""

    return report.strip()

# Example usage
patient_info = {
    "patient_id": "patient_123",
    "name": "John Doe",
    "age": 45,
    "gender": "Male",
    "medical_history": ["Hypertension", "Smoking History"]
}

symptoms = [
    {"name": "Chest pain", "severity": "moderate", "duration": "intermittent", "onset_date": "20 Sep 2025"},
    {"name": "Shortness of breath", "severity": "mild", "duration": "constant", "onset_date": "20 Sep 2025"},
    {"name": "Fatigue", "severity": "mild", "onset_date": "20 Sep 2025"}
]


possible_conditions = [
    "Cardiovascular concerns (e.g., acute coronary syndrome)",
    "Review and optimization of current medications",
    "Smoking cessation counseling and support"
]

urgency_level = "Red"

print(generate_medical_report(patient_info, symptoms, possible_conditions, urgency_level))
