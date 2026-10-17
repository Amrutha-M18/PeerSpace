import re


def tag_post(post, skills):
    """Post text + manual tags -> set of skill_ids."""
    text = (post["title"] + " " + post["description"]).lower()
    tags = set(post.get("tags", []))
    for skill_id, info in skills.items():
        for alias in info["aliases"]:
            if re.search(r"\b" + re.escape(alias) + r"\b", text):
                tags.add(skill_id)
                break
    return tags
