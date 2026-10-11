"""Bonus feature services: BMI, tips, hospitals, reminders."""

from __future__ import annotations

from datetime import date
from typing import List

from app.utils.helpers import HEALTH_TIPS


def calculate_bmi(height_cm: float, weight_kg: float) -> dict:
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    if bmi < 18.5:
        category, advice = "Underweight", "Consider a nutrient-rich diet and consult a clinician."
    elif bmi < 25:
        category, advice = "Normal", "Maintain balanced nutrition and regular physical activity."
    elif bmi < 30:
        category, advice = "Overweight", "Focus on diet quality, portion control, and daily movement."
    else:
        category, advice = "Obese", "Speak with a healthcare professional about a safe weight plan."
    return {"bmi": bmi, "category": category, "advice": advice}


def tip_of_the_day() -> dict:
    idx = date.today().toordinal() % len(HEALTH_TIPS)
    tip = HEALTH_TIPS[idx]
    return {"tip": tip["tip"], "category": tip["category"], "date": date.today().isoformat()}


def nearby_hospitals_placeholder(city: str = "Your City") -> List[dict]:
    return [
        {
            "name": f"{city} General Hospital",
            "address": f"12 Health Avenue, {city}",
            "phone": "+91-1800-111-222",
            "distance_km": 2.4,
            "specialties": ["Emergency", "Cardiology", "Pediatrics"],
        },
        {
            "name": "Aarogya Multispecialty Clinic",
            "address": f"88 Wellness Road, {city}",
            "phone": "+91-1800-333-444",
            "distance_km": 4.1,
            "specialties": ["General Medicine", "Diagnostics", "Nutrition"],
        },
        {
            "name": "CarePlus Trauma Center",
            "address": f"5 Emergency Blvd, {city}",
            "phone": "+91-1800-555-666",
            "distance_km": 6.8,
            "specialties": ["Trauma", "ICU", "Surgery"],
        },
    ]


def simple_symptom_check(symptoms: List[str], severity: str = "moderate") -> dict:
    joined = ", ".join(symptoms)
    urgency = "routine"
    advice = "Monitor your symptoms and rest. If they persist beyond a few days, consult a doctor."
    lowered = [s.lower() for s in symptoms]
    emergency_flags = {"chest pain", "can't breathe", "cannot breathe", "unconscious", "severe bleeding"}
    if any(any(f in s for f in emergency_flags) for s in lowered) or severity == "severe":
        urgency = "emergency"
        advice = "Seek emergency care immediately. Call local emergency services."
    elif severity == "mild":
        urgency = "self-care"
        advice = "Try rest, hydration, and over-the-counter supportive care as appropriate."

    return {
        "symptoms": symptoms,
        "summary": f"You reported: {joined}.",
        "urgency": urgency,
        "advice": advice,
        "disclaimer": "Educational only — not a diagnosis.",
    }


MEDICAL_NEWS = [
    {
        "title": "WHO emphasizes preventive care for noncommunicable diseases",
        "summary": "Lifestyle changes remain the strongest lever against diabetes and hypertension.",
        "tag": "Public Health",
    },
    {
        "title": "New guidance on adult vaccination schedules",
        "summary": "Updated recommendations highlight influenza and pneumococcal protection.",
        "tag": "Vaccines",
    },
    {
        "title": "Sleep hygiene linked to better metabolic health",
        "summary": "Recent reviews connect consistent sleep with lower cardiovascular risk.",
        "tag": "Wellness",
    },
]
