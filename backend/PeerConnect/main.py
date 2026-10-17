import json
from pathlib import Path

from matcher import rank_experts

DATA_DIR = Path(__file__).parent / "data"


def load(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def main():
    skills, users, posts = load("skills.json"), load("users.json"), load("posts.json")
    for post in posts:
        tags, top = rank_experts(post, users, skills)
        print(f"\n[{post['post_id']}] {post['title']}  (learner level {post['level']})")
        print("  Tags:", sorted(tags) if tags else "none found")
        if not top:
            print("  No matching experts.")
        for i, (name, s, b) in enumerate(top, 1):
            print(f"  {i}. {name:6} {s}  {b}")


if __name__ == "__main__":
    main()
