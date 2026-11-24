"""Unit tests for the matching module. No database needed."""

from backend.matching import Requirement, parse_requirements, rank_users, score_user

REACT, PYTHON, FIGMA = 1, 2, 3


def test_full_match_scores_100():
    result = score_user({REACT: 4, PYTHON: 3}, [Requirement(REACT, 3), Requirement(PYTHON, 2)])
    assert result.score == 100
    assert result.eligible


def test_partial_credit_for_lower_level():
    # React fully met, Python at 1 of 2 -> (1 + 0.5) / 2 = 75
    result = score_user({REACT: 4, PYTHON: 1}, [Requirement(REACT, 3), Requirement(PYTHON, 2)])
    assert result.score == 75


def test_no_requirements_scores_zero():
    assert score_user({REACT: 5}, []).score == 0


# 1. Must-have filter

def test_missing_must_have_makes_user_ineligible():
    result = score_user({PYTHON: 5}, [Requirement(REACT, 3, must_have=True), Requirement(PYTHON, 2)])
    assert not result.eligible
    assert result.missing_must_haves == [REACT]


def test_must_have_below_level_is_missing():
    result = score_user({REACT: 2}, [Requirement(REACT, 3, must_have=True)])
    assert not result.eligible


def test_ineligible_users_rank_below_eligible_ones():
    requirements = [Requirement(REACT, 3, must_have=True), Requirement(PYTHON, 3)]
    ranking = rank_users({10: {PYTHON: 5}, 20: {REACT: 3}}, requirements)
    assert [user_id for user_id, _ in ranking] == [20, 10]


# 4. Complementarity

def test_skill_the_team_already_has_counts_less():
    requirements = [Requirement(REACT, 3), Requirement(PYTHON, 3)]
    team = [{PYTHON: 4}]  # the team already has Python
    react_dev = score_user({REACT: 4}, requirements, team)
    python_dev = score_user({PYTHON: 4}, requirements, team)
    assert react_dev.score > python_dev.score  # fills the gap -> ranks higher
    assert react_dev.score == 80.0             # 1 / (1 + 0.25)


# 5. Owner's focus filter

def test_focus_skills_get_more_weight():
    requirements = [Requirement(REACT, 3), Requirement(FIGMA, 3)]
    designer = {FIGMA: 4}
    assert score_user(designer, requirements).score == 50
    assert score_user(designer, requirements, focus_skill_ids={FIGMA}).score == round(100 * 2 / 3, 1)


def test_focus_changes_the_ranking():
    requirements = [Requirement(REACT, 3), Requirement(FIGMA, 3)]
    candidates = {1: {REACT: 4}, 2: {FIGMA: 4, REACT: 1}}
    assert rank_users(candidates, requirements)[0][0] == 2
    assert rank_users(candidates, requirements, focus_skill_ids={REACT})[0][0] == 1


def test_focus_overrides_team_coverage():
    requirements = [Requirement(REACT, 3), Requirement(PYTHON, 3)]
    team = [{PYTHON: 4}]
    python_dev = score_user({PYTHON: 4}, requirements, team, focus_skill_ids={PYTHON})
    assert python_dev.score == round(100 * 2 / 3, 1)  # Python counts 2, React 1


def test_gaining_a_skill_never_lowers_the_score():
    requirements = [Requirement(REACT, 3), Requirement(PYTHON, 2, must_have=True)]
    before = score_user({REACT: 2}, requirements)
    after = score_user({REACT: 2, PYTHON: 2}, requirements)
    assert after.score >= before.score


def test_parse_requirements_accepts_both_formats():
    parsed = parse_requirements([{"skill_id": 1, "min_level": 3, "must_have": True}, 2])
    assert parsed == [Requirement(1, 3, True), Requirement(2, 1, False)]
    assert parse_requirements(None) == []
