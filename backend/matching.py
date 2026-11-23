"""Score how well a user fits a team. Pure Python: no database, no FastAPI.

Three ideas, applied in this order:

1. Must-have filter
   A required skill marked `must_have` is a hard rule. A user below its
   minimum level is marked not eligible (they still get a score so the owner
   can see how close they were).

2. Complementarity
   A skill the current team members already cover is worth less, because
   another person with it adds little. Skills the team lacks count fully.

3. Focus weighting (optional, chosen by the owner)
   The owner can pick a subset of the required skills to focus on.
   Those skills count FOCUS_WEIGHT times more in the score, and the owner's
   choice overrides complementarity: a focused skill is never discounted,
   even if the team already has it.

Per skill, a user earns partial credit: level 2 against a required level 4
earns half. Credit never goes above 1, so being far above the requirement
does not make up for missing another skill.

Score = 100 * (sum of credit x weight) / (sum of weight), over required skills.
"""

from dataclasses import dataclass, field

FOCUS_WEIGHT = 2.0     # skills in the owner's focus subset count double
COVERED_WEIGHT = 0.25  # skills the team already has count a quarter


@dataclass
class Requirement:
    """One skill a team asks for (stored in teams.needed_skills)."""
    skill_id: int
    min_level: int = 1
    must_have: bool = False


@dataclass
class SkillResult:
    skill_id: int
    required_level: int
    user_level: int
    credit: float          # 0.0 to 1.0
    weight: float
    team_covers: bool
    in_focus: bool


@dataclass
class MatchResult:
    score: float                                   # 0 to 100
    eligible: bool                                 # False if a must-have is missing
    missing_must_haves: list[int] = field(default_factory=list)
    skills: list[SkillResult] = field(default_factory=list)


def score_user(
    user_skills: dict[int, int],
    requirements: list[Requirement],
    team_member_skills: list[dict[int, int]] | None = None,
    focus_skill_ids: set[int] | None = None,
) -> MatchResult:
    """
    user_skills:        {skill_id: level} for the user being scored
    requirements:       what the team needs
    team_member_skills: one {skill_id: level} dict per current team member
    focus_skill_ids:    optional owner filter: skills to give more weight
    """
    team_member_skills = team_member_skills or []
    focus_skill_ids = focus_skill_ids or set()

    results: list[SkillResult] = []
    missing: list[int] = []
    earned = 0.0
    total = 0.0

    for req in requirements:
        min_level = max(1, req.min_level)
        user_level = user_skills.get(req.skill_id, 0)

        # 1. Must-have filter
        if req.must_have and user_level < min_level:
            missing.append(req.skill_id)

        # 2. Complementarity: does someone in the team already meet this requirement?
        team_level = max((member.get(req.skill_id, 0) for member in team_member_skills), default=0)
        team_covers = team_level >= min_level

        # 3. Focus weighting (the owner's choice wins over complementarity)
        in_focus = req.skill_id in focus_skill_ids
        if in_focus:
            weight = FOCUS_WEIGHT
        elif team_covers:
            weight = COVERED_WEIGHT
        else:
            weight = 1.0

        credit = min(user_level / min_level, 1.0)
        earned += credit * weight
        total += weight
        results.append(SkillResult(req.skill_id, min_level, user_level, round(credit, 2), weight, team_covers, in_focus))

    score = round(100 * earned / total, 1) if total else 0.0
    return MatchResult(score=score, eligible=not missing, missing_must_haves=missing, skills=results)


def parse_requirements(needed_skills: list) -> list[Requirement]:
    """Read teams.needed_skills.

    Expected format:  [{"skill_id": 3, "min_level": 3, "must_have": true}, ...]
    A plain list of skill IDs ([3, 7]) also works: level 1, not must-have.
    """
    requirements = []
    for item in needed_skills or []:
        if isinstance(item, int):
            requirements.append(Requirement(skill_id=item))
        elif isinstance(item, dict) and "skill_id" in item:
            requirements.append(Requirement(
                skill_id=int(item["skill_id"]),
                min_level=int(item.get("min_level", 1)),
                must_have=bool(item.get("must_have", False)),
            ))
    return requirements


def rank_users(
    candidates: dict[int, dict[int, int]],
    requirements: list[Requirement],
    team_member_skills: list[dict[int, int]] | None = None,
    focus_skill_ids: set[int] | None = None,
) -> list[tuple[int, MatchResult]]:
    """Score many users at once. Eligible users first, then by score (highest first)."""
    scored = [
        (user_id, score_user(skills, requirements, team_member_skills, focus_skill_ids))
        for user_id, skills in candidates.items()
    ]
    return sorted(scored, key=lambda pair: (pair[1].eligible, pair[1].score), reverse=True)
