"""
AI Prediction Model — Rule-based scoring engine that mimics
a trained ML classifier (Random Forest + Regression ensemble).
In production, replace score() with a joblib-loaded sklearn model.
"""

def predict_grade(features: dict) -> dict:
    """
    features:
        prev_gpa        float  0–4
        attendance      float  0–100
        assignment_rate float  0–100
        study_hours     float  hours/week
    returns dict with grade, confidence, pass_probability, risk_level, main_factor, tips
    """
    percentage = float(features.get('percentage', 60))
    att   = float(features.get('attendance', 75))
    asgn  = float(features.get('assignment_rate', 75))
    hrs   = float(features.get('study_hours', 10))

    # Feature weights (mimic Random Forest importance)
    score = (
    (percentage / 100) * 0.38 +
    (att / 100) * 0.28 +
    (asgn / 100) * 0.20 +
    min(hrs / 20, 1.0) * 0.14
)

    # Determine grade band
    if score >= 0.88:
        grade = 'A'; conf = 94; pass_prob = 99
    elif score >= 0.78:
        grade = 'A-'; conf = 91; pass_prob = 97
    elif score >= 0.70:
        grade = 'B+'; conf = 88; pass_prob = 95
    elif score >= 0.62:
        grade = 'B'; conf = 85; pass_prob = 91
    elif score >= 0.54:
        grade = 'C+'; conf = 81; pass_prob = 84
    elif score >= 0.46:
        grade = 'C'; conf = 78; pass_prob = 76
    elif score >= 0.38:
        grade = 'D'; conf = 74; pass_prob = 52
    else:
        grade = 'F'; conf = 82; pass_prob = 18

    # Risk classification
    if score >= 0.70:
        risk_level = 'none'
    elif score >= 0.54:
        risk_level = 'low'
    elif score >= 0.42:
        risk_level = 'medium'
    elif score >= 0.30:
        risk_level = 'high'
    else:
        risk_level = 'critical'

    # Identify weakest factor
    factors = {
    'Percentage': percentage / 100,
    'Attendance': att / 100,
    'Assignment completion': asgn / 100,
    'Study hours': min(hrs / 20, 1.0),
}
    main_factor = min(factors, key=factors.get)

    # Personalised tips
    tips = []
    if att < 75:
        tips.append('Attendance is below 75% — this is the strongest predictor of failure.')
    if asgn < 70:
        tips.append('Submit all assignments on time; aim for 90%+ completion rate.')
    if hrs < 10:
        tips.append('Increase dedicated study time to at least 15 hours per week.')
    if percentage < 50:
        tips.append('Academic counselling and subject-wise tutoring is recommended.')
    if risk_level in ('high', 'critical'):
        tips.append('Immediate intervention: contact your faculty mentor or HOD.')
    if not tips:
        tips.append('Keep up the great work and maintain current study habits.')

    return {
        'grade':          grade,
        'score':          round(score, 4),
        'confidence':     conf,
        'pass_probability': pass_prob,
        'risk_level':     risk_level,
        'main_factor':    main_factor,
        'tips':           tips,
    }


# ── ML Extension (swap in when sklearn is available) ─────────────────────────
#
# import joblib, numpy as np
# _model = joblib.load('models/student_rf_model.pkl')
# _scaler = joblib.load('models/scaler.pkl')
#
# def predict_grade_ml(features):
#     X = np.array([[features['prev_gpa'], features['attendance'],
#                    features['assignment_rate'], features['study_hours']]])
#     X_scaled = _scaler.transform(X)
#     grade = _model.predict(X_scaled)[0]
#     proba = _model.predict_proba(X_scaled).max()
#     return {'grade': grade, 'confidence': round(proba*100), ...}
