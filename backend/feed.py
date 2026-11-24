"""Personalised opportunity feed: how well an opportunity fits a user's interests.

An interest matches an opportunity in two ways:
  - strongly (3 points) when the interest, or a word close to it, appears in the title,
    description or organizer, e.g. "Football" in "Inter-Hostel Football League";
  - loosely (1 point) when it simply fits the category, e.g. "Cycling" for any sport.
Opportunities are sorted by points, then by how soon they start.
"""

import re
from dataclasses import dataclass, field
from datetime import date

from .models import Opportunity

STRONG, LOOSE = 3, 1

# Interests (names from seed_data/hobbies.txt) that fit each category.
CATEGORY_INTERESTS = {
    "hackathon": {"Open Source", "Entrepreneurship", "Puzzles", "Gaming"},
    "course project": {"Reading", "Open Source"},
    "study group": {"Reading", "Puzzles", "Quizzing", "Chess", "Debating"},
    "trek": {"Trekking", "Camping", "Travel", "Birdwatching", "Photography", "Running", "Cycling"},
    "sport": {
        "Cricket", "Football", "Badminton", "Basketball", "Volleyball", "Table Tennis", "Tennis", "Kabaddi",
        "Athletics", "Running", "Swimming", "Cycling", "Gym and Fitness", "Yoga", "Martial Arts",
    },
    "other": set(),
}

# Other words that count as mentioning an interest (the interest's own name always counts).
INTEREST_WORDS = {
    "Trekking": ["trek", "hike", "hiking"],
    "Camping": ["camp", "overnight"],
    "Astronomy": ["stars", "telescope", "space"],
    "Football": ["soccer"],
    "Entrepreneurship": ["startup", "pitch", "founder", "founders"],
    "Open Source": ["open-source", "github"],
    "Gaming": ["game", "games"],
    "Photography": ["photo", "photos", "camera"],
    "Film Making": ["film", "movie", "video"],
    "Volunteering": ["volunteer", "ngo", "social"],
    "Debating": ["debate"],
    "Quizzing": ["quiz"],
    "Puzzles": ["puzzle", "problem-solving"],
    "Public Speaking": ["speaking"],
    "Running": ["run", "marathon"],
    "Cycling": ["cycle", "bike"],
}


@dataclass
class Match:
    score: int = 0
    interests: list[str] = field(default_factory=list)  # strongest first


def mentions(text: str, interest: str) -> bool:
    words = [interest, *INTEREST_WORDS.get(interest, [])]
    return any(re.search(rf"(?<![\w-]){re.escape(word.lower())}(?![\w-])", text) for word in words)


def match_interests(opportunity: Opportunity, interests: list[str]) -> Match:
    text = " ".join(filter(None, [opportunity.title, opportunity.description, opportunity.organizer])).lower()
    related = CATEGORY_INTERESTS.get(opportunity.category, set())
    strong = [name for name in interests if mentions(text, name)]
    loose = [name for name in interests if name in related and name not in strong]
    return Match(score=STRONG * len(strong) + LOOSE * len(loose), interests=strong + loose)


def is_over(opportunity: Opportunity, today: date) -> bool:
    last_day = opportunity.ends_on or opportunity.starts_on
    return last_day is not None and last_day < today


def sort_key(opportunity: Opportunity, match: Match):
    """Best match first, then the soonest start (undated last), then oldest listing."""
    return (-match.score, opportunity.starts_on is None, opportunity.starts_on or date.max, opportunity.id)
