import pytest

from app.utils.helpers import detect_emergency


@pytest.mark.parametrize(
    "text",
    [
        "I want to kill myself",
        "I can't breathe",
        "My dad is having a heart attack",
        "I have severe chest pain",
        "my throat is swelling after a bee sting",
        "he took too many pills",
        "my baby is unconscious",
    ],
)
def test_emergencies_are_flagged(text):
    assert detect_emergency(text)[0]


@pytest.mark.parametrize(
    "text",
    [
        "What is a heart attack?",
        "What are the signs of a stroke?",
        "What causes seizures?",
        "What is anaphylaxis?",
        "What is glaucoma?",
    ],
)
def test_informational_questions_are_not_flagged(text):
    assert not detect_emergency(text)[0]
