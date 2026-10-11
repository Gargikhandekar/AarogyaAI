"""Utility helpers: text cleaning, emergency detection, categories, logging."""

from __future__ import annotations

import logging
import re
from typing import Optional, Tuple

DISCLAIMER = (
    "This information is for educational purposes only. "
    "Please consult a licensed healthcare professional for medical advice."
)

MEDICAL_CATEGORIES = [
    "Symptoms",
    "Diseases",
    "Medicines",
    "First Aid",
    "Nutrition",
    "Mental Health",
    "Pregnancy",
    "Child Care",
    "Fitness",
]

CATEGORY_KEYWORDS = {
    "Symptoms": ["symptom", "pain", "ache", "fever", "cough", "nausea", "dizziness", "rash"],
    "Diseases": ["disease", "diabetes", "hypertension", "cancer", "asthma", "infection", "virus"],
    "Medicines": ["medicine", "drug", "dosage", "tablet", "antibiotic", "prescription", "side effect"],
    "First Aid": ["first aid", "bleed", "burn", "fracture", "cpr", "choking", "wound", "sprain"],
    "Nutrition": ["nutrition", "diet", "vitamin", "protein", "calorie", "food", "eat", "obesity"],
    "Mental Health": ["anxiety", "depression", "stress", "mental", "sleep", "panic", "therapy"],
    "Pregnancy": ["pregnan", "prenatal", "trimester", "labor", "fetal", "maternity"],
    "Child Care": ["baby", "infant", "child", "pediatric", "vaccine", "toddler", "newborn"],
    "Fitness": ["exercise", "workout", "fitness", "cardio", "muscle", "yoga", "stretch"],
}

EMERGENCY_PATTERNS = [
    (r"\bchest\s+pain\b", "Chest pain can be a sign of a heart attack."),
    (r"\b(kill\s+(my)?self|suicide|end\s+my\s+life|want\s+to\s+die)\b", "Suicidal thoughts require immediate help."),
    (r"\b(cannot|can't|cant)\s+breathe\b", "Difficulty breathing is a medical emergency."),
    (r"\b(baby|child|infant).{0,40}\bunconscious\b", "An unconscious infant/child needs emergency care."),
    (r"\bunconscious\b", "Loss of consciousness is a medical emergency."),
    (r"\b(severe|heavy)\s+bleeding\b", "Severe bleeding requires emergency care."),
    (r"\bstroke\b.{0,20}\b(symptoms|signs|now)\b", "Possible stroke symptoms need immediate attention."),
    (r"\bheart\s+attack\b", "Suspected heart attack requires emergency services."),
    (r"\boverdose\b", "A possible overdose is a medical emergency."),
    (r"\bseizure\b", "Active seizures may require emergency assistance."),
    (r"\banalphylaxis\b|\ballergic\s+reaction\b.{0,30}\b(throat|swelling|breath)", "Severe allergic reactions need emergency care."),
]

EMERGENCY_RESPONSE = """🚨 **EMERGENCY WARNING**

Your message may indicate a **medical emergency**.

**Please take action immediately:**
1. Call your local emergency number (**112** in India / **911** in the US)
2. Go to the nearest emergency room
3. Do not wait for an online chatbot response

{reason}

If you are in emotional distress or having suicidal thoughts:
- **India:** AASRA +91-9820466726 | Vandrevala Foundation 9999666555
- **International:** https://www.iasp.info/suicidalthoughts/

---
*Aarogya AI cannot provide emergency medical care. Seek professional help now.*
"""

SMART_SUGGESTIONS = [
    "I have a headache",
    "What causes diabetes?",
    "How to reduce fever?",
    "What is hypertension?",
    "Best foods for heart health",
    "Symptoms of vitamin D deficiency",
    "How to manage anxiety naturally?",
    "First aid for burns",
    "Safe exercises during pregnancy",
    "Child fever home care tips",
]

HEALTH_TIPS = [
    {"tip": "Drink at least 8 glasses of water daily to stay hydrated.", "category": "Nutrition"},
    {"tip": "Aim for 7–9 hours of quality sleep each night.", "category": "Mental Health"},
    {"tip": "Walk briskly for 30 minutes most days of the week.", "category": "Fitness"},
    {"tip": "Wash your hands thoroughly before meals to prevent infections.", "category": "First Aid"},
    {"tip": "Include colorful vegetables in every meal for micronutrients.", "category": "Nutrition"},
    {"tip": "Practice deep breathing for 5 minutes when stressed.", "category": "Mental Health"},
    {"tip": "Schedule regular health check-ups even when you feel well.", "category": "Diseases"},
    {"tip": "Limit screen time before bed for better sleep quality.", "category": "Mental Health"},
]


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("aarogya")


logger = setup_logging()


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.,?!'\"%-:/()]", "", text)
    return text


def detect_emergency(text: str) -> Tuple[bool, Optional[str]]:
    lowered = text.lower()
    for pattern, reason in EMERGENCY_PATTERNS:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return True, reason
    return False, None


def infer_category(text: str) -> str:
    lowered = text.lower()
    scores = {
        cat: sum(1 for kw in kws if kw in lowered) for cat, kws in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Symptoms"


def build_chat_title(message: str) -> str:
    cleaned = clean_text(message)
    return cleaned[:60] + ("…" if len(cleaned) > 60 else "")
