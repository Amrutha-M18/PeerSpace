MAX_ACTIVE = 3  # request cap per expert


def score(expert, post, tags):
    """One expert + one post -> (score 0..1, breakdown). Returns None if expert can't help."""
    learner_level = post["level"]
    # skills the expert can teach AND is ahead of the learner in
    matched = [s for s in expert["skills"]
               if s["skill_id"] in tags and s["open_to_teach"] and s["level"] > learner_level]
    active = expert.get("active_requests", 0)
    if not matched or expert["user_id"] == post["author_id"] or active >= MAX_ACTIVE:
        return None

    coverage = len(matched) / len(tags)

    avg_gap = sum(s["level"] - learner_level for s in matched) / len(matched)
    level_gap = 1.0 if avg_gap <= 2 else max(0.0, 1 - 0.25 * (avg_gap - 2))  # too far ahead = less ideal

    # Bayesian average: new experts start near 3.5/5 instead of jumping to the top
    n, avg = expert.get("rating_count", 0), expert.get("rating_avg", 0)
    reputation = ((avg * n + 3.5 * 3) / (n + 3)) / 5

    load = active / MAX_ACTIVE

    total = 0.5 * coverage + 0.3 * level_gap + 0.2 * reputation - 0.2 * load
    breakdown = {"coverage": round(coverage, 2), "level_gap": round(level_gap, 2),
                 "reputation": round(reputation, 2), "load": round(load, 2)}
    return round(max(0.0, total), 2), breakdown
