from tagger import tag_post
from scorer import score


def rank_experts(post, users, skills, k=3):
    """Post + all users -> (tags, top k [(name, score, breakdown)])."""
    tags = tag_post(post, skills)
    if not tags:
        return tags, []
    results = []
    for user in users:
        r = score(user, post, tags)
        if r:
            results.append((user["name"], r[0], r[1]))
    results.sort(key=lambda x: x[1], reverse=True)
    return tags, results[:k]
