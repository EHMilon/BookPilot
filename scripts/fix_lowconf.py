"""Hand overrides for empty + misclassified tags from the rule pass.

Usage: python3 scripts/fix_lowconf.py [--write] (dry-run default)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "book_manifest.json"

OVERRIDES = {
    "a-mans-search-for-ultimate-meaning": ["Psychology", "Philosophy", "Happiness & Resilience"],
    "african-wisdom": ["Culture & Society", "Philosophy"],
    "character-is-destiny": ["Memoir & Biography", "Self-Help"],
    "civil-disobedience": ["Philosophy", "Culture & Society"],
    "confessions-of-a-public-speaker": ["Business & Leadership", "Communication & Relationships"],
    "didnt-see-it-coming": ["Self-Help", "Mental Health & Wellbeing"],
    "goodbye-things": ["Lifestyle & Minimalism"],
    "karma-yoga": ["Mindfulness & Spirituality", "Philosophy"],
    "mistakes-were-made-but-not-by-me": ["Psychology"],
    "overcoming-unwanted-intrusive-thoughts": ["Mental Health & Wellbeing", "Psychology"],
    "spark-joy": ["Lifestyle & Minimalism"],
    "ted-talks-guide-to-public-speaking": ["Business & Leadership", "Communication & Relationships"],
    "thanks-for-the-feedback": ["Communication & Relationships", "Business & Leadership"],
    "the-aladdin-factor": ["Self-Help"],
    "the-dichotomy-of-leadership": ["Business & Leadership"],
    "168-hours": ["Productivity & Habits"],
    "a-woman-makes-a-plan": ["Memoir & Biography", "Self-Help"],
    "beyond-the-last-path": ["Memoir & Biography", "History & Classics"],
    "bread-and-wine": ["Memoir & Biography", "Mindfulness & Spirituality"],
    "critique-of-pure-reason": ["Philosophy"],
    "difficult-conversations": ["Communication & Relationships", "Business & Leadership"],
    "discipline-is-destiny": ["Philosophy", "Self-Help"],
    "discipline-is-destiny-ryan-holiday": ["Philosophy", "Self-Help"],
    "enchiridion": ["Philosophy", "Self-Help"],
    "escape-from-freedom": ["Philosophy", "Psychology"],
    "everything-is-fcked": ["Self-Help", "Philosophy"],
    "finding-your-element": ["Education & Learning", "Creativity & Art"],
    "freedom-from-the-known": ["Philosophy", "Mindfulness & Spirituality"],
    "gestalt-therapy-verbatim": ["Psychology", "Mental Health & Wellbeing"],
    "great-by-choice": ["Business & Leadership"],
    "groundwork-of-the-metaphysics-of-morals": ["Philosophy"],
    "hagakure": ["Philosophy", "History & Classics"],
    "how-to-be-a-stoic": ["Philosophy", "Happiness & Resilience"],
    "how-to-develop-self-confidence": ["Self-Help"],
    "how-to-win-an-argument": ["Communication & Relationships", "Psychology"],
    "i-and-thou": ["Philosophy", "Communication & Relationships"],
    "in-and-out-of-the-garbage-pail": ["Memoir & Biography", "Psychology"],
    "influence": ["Psychology", "Business & Leadership"],
    "influence-the-psychology-of-persuasion": ["Psychology", "Business & Leadership"],
    "into-thin-air": ["Memoir & Biography", "Travel & Adventure"],
    "iron-john": ["Psychology", "Philosophy"],
    "lateral-thinking": ["Psychology", "Creativity & Art"],
    "life-is-messy-god-is-good": ["Mindfulness & Spirituality", "Self-Help"],
    "lifes-golden-ticket": ["Fiction & Literature", "Self-Help"],
    "living-in-the-light-of-death": ["Mindfulness & Spirituality", "Philosophy"],
    "made-to-stick": ["Communication & Relationships", "Business & Leadership"],
    "mating-in-captivity": ["Communication & Relationships", "Psychology"],
    "mencius": ["Philosophy", "History & Classics"],
}

UNSET = {
    "the-little-prince": ["Tales & Fables", "Philosophy"],
    "siddhartha": ["Fiction & Literature", "Mindfulness & Spirituality"],
    "tuesdays-with-morrie": ["Memoir & Biography", "Philosophy"],
    "sapiens": ["History & Classics", "Science & Technology"],
}


def main():
    write = "--write" in sys.argv
    m = json.loads(MANIFEST.read_text())
    allowed = set(m["tags"])
    n = 0
    for b in m["books"]:
        if b["id"] in OVERRIDES:
            tags = OVERRIDES[b["id"]]
        elif b["id"] in UNSET:
            tags = UNSET[b["id"]]
        else:
            continue
        assert all(t in allowed for t in tags), b["id"]
        if write:
            b["tags"] = tags
            b["updatedAt"] = "2026-10-30"
        n += 1
    print(f"{'APPLIED' if write else 'dry-run'}: {n} overrides")
    if write:
        MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(main())
