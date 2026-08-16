import re

def parse_prescription_text(text):
    """
    Parse OCR text from prescription to extract relevant health metrics.
    Returns a dict with keys like 'glucose', 'hba1c', etc.
    """
    parsed = {}
    text = text.lower()

    # Extract glucose (mg/dL) - multiple patterns
    glucose_patterns = [
        r'glucose[:\s]*(\d+)',
        r'blood\s+sugar[:\s]*(\d+)',
        r'bs[:\s]*(\d+)',
        r'fasting\s+glucose[:\s]*(\d+)',
        r'random\s+glucose[:\s]*(\d+)'
    ]
    for pattern in glucose_patterns:
        glucose_match = re.search(pattern, text)
        if glucose_match:
            parsed['glucose'] = float(glucose_match.group(1))
            break

    # Extract HbA1c (%) - multiple patterns
    hba1c_patterns = [
        r'hba1c[:\s]*(\d+\.?\d*)',
        r'a1c[:\s]*(\d+\.?\d*)',
        r'glycosylated\s+hemoglobin[:\s]*(\d+\.?\d*)',
        r'hemoglobin\s+a1c[:\s]*(\d+\.?\d*)'
    ]
    for pattern in hba1c_patterns:
        hba1c_match = re.search(pattern, text)
        if hba1c_match:
            parsed['hba1c'] = float(hba1c_match.group(1))
            break

    # Extract blood pressure (systolic/diastolic)
    bp_match = re.search(r'(\d+)/(\d+)', text)
    if bp_match:
        systolic = int(bp_match.group(1))
        diastolic = int(bp_match.group(2))
        if 80 <= systolic <= 200 and 50 <= diastolic <= 120:
            parsed['blood_pressure'] = (systolic, diastolic)

    # Extract BMI
    bmi_match = re.search(r'bmi[:\s]*(\d+\.?\d*)', text)
    if bmi_match:
        bmi = float(bmi_match.group(1))
        if 10 <= bmi <= 50:
            parsed['bmi'] = bmi

    # Extract age
    age_match = re.search(r'age[:\s]*(\d+)', text)
    if age_match:
        age = int(age_match.group(1))
        if 0 <= age <= 120:
            parsed['age'] = age

    # Extract insulin
    insulin_match = re.search(r'insulin[:\s]*(\d+)', text)
    if insulin_match:
        insulin = int(insulin_match.group(1))
        if 0 <= insulin <= 1000:
            parsed['insulin'] = insulin

    # Extract skin thickness
    skin_match = re.search(r'skin\s+thickness[:\s]*(\d+)', text)
    if skin_match:
        skin = int(skin_match.group(1))
        if 0 <= skin <= 100:
            parsed['skin_thickness'] = skin

    # Extract pregnancies
    preg_match = re.search(r'pregnanc(?:y|ies)[:\s]*(\d+)', text)
    if preg_match:
        preg = int(preg_match.group(1))
        if 0 <= preg <= 20:
            parsed['pregnancies'] = preg

    # Extract diabetes pedigree function (if mentioned)
    dpf_match = re.search(r'pedigree[:\s]*(\d+\.?\d*)', text)
    if dpf_match:
        dpf = float(dpf_match.group(1))
        if 0 <= dpf <= 3.0:
            parsed['diabetes_pedigree_function'] = dpf

    return parsed

def probability_to_category(prob):
    """
    Categorize diabetes risk based on prediction probability.
    """
    if prob < 0.2:
        return "Very Low Risk"
    elif prob < 0.4:
        return "Low Risk"
    elif prob < 0.6:
        return "Medium Risk"
    elif prob < 0.8:
        return "High Risk"
    else:
        return "Very High Risk"

def suggest_foods(category):
    """
    Suggest foods based on risk category.
    Returns a list of dicts with 'name', 'desc', 'img'
    """
    suggestions = {
        "Very Low Risk": [
            {"name": "Leafy Greens", "desc": "Rich in vitamins and low in calories.", "img": "/static/images/greens.jpg"},
            {"name": "Whole Grains", "desc": "Provide sustained energy.", "img": "/static/images/grains.jpg"},
        ],
        "Low Risk": [
            {"name": "Leafy Greens", "desc": "Rich in vitamins and low in calories.", "img": "/static/images/greens.jpg"},
            {"name": "Whole Grains", "desc": "Provide sustained energy.", "img": "/static/images/grains.jpg"},
        ],
        "Medium Risk": [
            {"name": "Lean Proteins", "desc": "Help maintain muscle mass.", "img": "/static/images/protein.jpg"},
            {"name": "Fruits", "desc": "Natural sugars with fiber.", "img": "/static/images/fruits.jpg"},
        ],
        "High Risk": [
            {"name": "Low-Carb Vegetables", "desc": "Minimize blood sugar spikes.", "img": "/static/images/veggies.jpg"},
            {"name": "Nuts", "desc": "Healthy fats and proteins.", "img": "/static/images/nuts.jpg"},
        ],
        "Very High Risk": [
            {"name": "Low-Carb Vegetables", "desc": "Minimize blood sugar spikes.", "img": "/static/images/veggies.jpg"},
            {"name": "Nuts", "desc": "Healthy fats and proteins.", "img": "/static/images/nuts.jpg"},
        ]
    }
    return suggestions.get(category, [])
