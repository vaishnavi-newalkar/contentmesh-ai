# analytics.py

import random
from typing import Dict


def get_metrics() -> Dict:
    """
    Simulates engagement metrics.
    In real-world, this would pull from APIs (Google Analytics, etc.)
    """
    return {
        "engagement_score": random.randint(70, 95),
        "click_through_rate": round(random.uniform(2.0, 10.0), 2),
        "open_rate": round(random.uniform(10.0, 40.0), 2),
        "conversion_rate": round(random.uniform(1.0, 5.0), 2),
    }


def analyze_performance(metrics: Dict) -> Dict:
    """
    Generates insights based on metrics.
    """
    suggestions = []

    if metrics["engagement_score"] < 75:
        suggestions.append("Improve storytelling and hooks")

    if metrics["click_through_rate"] < 5:
        suggestions.append("Use stronger CTA and headlines")

    if metrics["open_rate"] < 20:
        suggestions.append("Optimize subject lines or timing")

    if metrics["conversion_rate"] < 2:
        suggestions.append("Refine value proposition")

    return {
        "metrics": metrics,
        "suggestions": suggestions
    }


def adjust_strategy(metrics: Dict) -> Dict:
    """
    Suggests content strategy changes.
    """
    strategy = {
        "best_channel": "email",
        "recommended_format": "blog",
        "posting_time": "morning"
    }

    if metrics["engagement_score"] > 85:
        strategy["recommended_format"] = "short-form + reels"

    if metrics["click_through_rate"] > 7:
        strategy["best_channel"] = "social_media"

    return strategy