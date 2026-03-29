# guardrails.py

from typing import List, Dict

# You can expand this list based on your use case
FORBIDDEN_WORDS = [
    "guarantee",
    "100% safe",
    "no risk",
    "instant results",
    "risk-free",
]

# Tone / brand checks (optional)
DISCOURAGED_WORDS = [
    "cheap",
    "best ever",
    "unbelievable",
]

def check_rules(text: str) -> Dict:
    """
    Checks text for rule violations.
    Returns a dictionary with violations.
    """
    text_lower = text.lower()

    violations = {
        "forbidden": [],
        "discouraged": []
    }

    # Check forbidden words
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            violations["forbidden"].append(word)

    # Check discouraged tone
    for word in DISCOURAGED_WORDS:
        if word in text_lower:
            violations["discouraged"].append(word)

    return violations


def clean_content(text: str) -> str:
    """
    Cleans text by removing/replacing problematic words.
    """
    cleaned_text = text

    # Replace forbidden words
    for word in FORBIDDEN_WORDS:
        cleaned_text = cleaned_text.replace(word, "[REMOVED]")

    # Replace discouraged words (soft replacement)
    for word in DISCOURAGED_WORDS:
        cleaned_text = cleaned_text.replace(word, "[REPHRASE]")

    return cleaned_text


def is_compliant(violations: Dict) -> bool:
    """
    Returns True if no forbidden violations exist.
    """
    return len(violations.get("forbidden", [])) == 0