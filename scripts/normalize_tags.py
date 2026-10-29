"""Normalize free-text book tags to the curated top-level `tags` allowlist.

Reads book_manifest.json, dedupes books by id, drops the `feature`
pseudo-tag (collecting those ids into top-level `features`), maps every
remaining tag to the 27 canonical categories, writes the manifest back.

Usage: python3 scripts/normalize_tags.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "book_manifest.json"

CANONICAL_TAGS = [
    "Self-Help",
    "Psychology",
    "Philosophy",
    "Mindfulness & Spirituality",
    "Neuroscience & Brain",
    "Mental Health & Wellbeing",
    "Health & Nutrition",
    "Productivity & Habits",
    "Business & Leadership",
    "Finance & Wealth",
    "Communication & Relationships",
    "Creativity & Art",
    "Education & Learning",
    "Science & Technology",
    "Memoir & Biography",
    "History & Classics",
    "Nature & Environment",
    "Travel & Adventure",
    "Culture & Society",
    "Parenting & Family",
    "Happiness & Resilience",
    "Essays & Poetry",
    "Lifestyle & Minimalism",
    "Fiction & Literature",
    "Fantasy & Sci-Fi",
    "Mystery & Thriller",
    "Tales & Fables",
]

# Explicit old-tag (casefolded) -> canonical mapping.
TAG_MAP = {
    # Self-Help
    "self-help": "Self-Help", "personal development": "Self-Help",
    "personal growth": "Self-Help", "motivation": "Self-Help",
    "inspiration": "Self-Help", "empowerment": "Self-Help",
    "self-discovery": "Self-Help", "personal transformation": "Self-Help",
    "success": "Self-Help", "self-care": "Self-Help",
    "self-knowledge": "Self-Help", "new thought": "Self-Help",
    "mindset": "Self-Help", "character": "Self-Help", "virtue": "Self-Help",
    "practical wisdom": "Self-Help", "authenticity": "Self-Help",
    "presence": "Self-Help", "transformation": "Self-Help",
    "self-education": "Education & Learning",
    # Psychology
    "psychology": "Psychology", "behavioral economics": "Psychology",
    "cbt": "Psychology", "emotions": "Psychology",
    "emotional intelligence": "Psychology",
    "developmental psychology": "Psychology",
    "child psychology": "Psychology", "psychoanalysis": "Psychology",
    "attachment": "Psychology", "decision making": "Psychology",
    "decision-making": "Psychology", "critical thinking": "Education & Learning",
    # Philosophy
    "philosophy": "Philosophy", "stoicism": "Philosophy",
    "ethics": "Philosophy", "meaning": "Philosophy",
    "eastern philosophy": "Philosophy", "taoism": "Philosophy",
    "existential": "Philosophy", "metaphysics": "Philosophy",
    "logic": "Philosophy", "philosophy of mind": "Philosophy",
    "wisdom": "Philosophy", "wisdom literature": "Philosophy",
    "transcendentalism": "Philosophy", "confucianism": "Philosophy",
    "chinese philosophy": "Philosophy", "history of ideas": "Philosophy",
    # Mindfulness & Spirituality
    "spirituality": "Mindfulness & Spirituality",
    "mindfulness": "Mindfulness & Spirituality",
    "meditation": "Mindfulness & Spirituality",
    "buddhism": "Mindfulness & Spirituality",
    "yoga": "Mindfulness & Spirituality", "zen": "Mindfulness & Spirituality",
    "sufism": "Mindfulness & Spirituality",
    "tibetan buddhism": "Mindfulness & Spirituality",
    "botany": "Nature & Environment",
    "death": "Philosophy",
    "mortality": "Philosophy",
    "indigenous wisdom": "Culture & Society",
    "military": "Business & Leadership",
    "scotland": "Travel & Adventure",
    "ritual": "Mindfulness & Spirituality",
    "compassion": "Mindfulness & Spirituality",
    "christian living": "Mindfulness & Spirituality",
    # Neuroscience & Brain
    "neuroscience": "Neuroscience & Brain",
    "neurology": "Neuroscience & Brain",
    "neuroplasticity": "Neuroscience & Brain",
    "consciousness": "Neuroscience & Brain",
    "perception": "Neuroscience & Brain",
    "plasticity": "Neuroscience & Brain",
    "cognitive science": "Neuroscience & Brain",
    "interpersonal neurobiology": "Neuroscience & Brain",
    # Mental Health & Wellbeing
    "mental health": "Mental Health & Wellbeing",
    "anxiety": "Mental Health & Wellbeing",
    "depression": "Mental Health & Wellbeing",
    "wellness": "Mental Health & Wellbeing",
    "wellbeing": "Mental Health & Wellbeing",
    "well-being": "Mental Health & Wellbeing",
    "healing": "Mental Health & Wellbeing",
    "health & healing": "Mental Health & Wellbeing",
    "grief": "Mental Health & Wellbeing",
    "addiction": "Mental Health & Wellbeing",
    "addiction & recovery": "Mental Health & Wellbeing",
    "emotional health": "Mental Health & Wellbeing",
    "emotional education": "Mental Health & Wellbeing",
    "adolescence": "Mental Health & Wellbeing",
    "adolescent development": "Mental Health & Wellbeing",
    # Health & Nutrition
    "health": "Health & Nutrition", "nutrition": "Health & Nutrition",
    "fitness": "Health & Nutrition", "longevity": "Health & Nutrition",
    "gut health": "Health & Nutrition", "fasting": "Health & Nutrition",
    "mediterranean diet": "Health & Nutrition",
    "ayurveda": "Health & Nutrition",
    "movement science": "Health & Nutrition",
    "biomechanics": "Health & Nutrition", "medicine": "Health & Nutrition",
    "energy management": "Health & Nutrition",
    "weight loss": "Health & Nutrition",
    # Productivity & Habits
    "productivity": "Productivity & Habits",
    "habits": "Productivity & Habits", "focus": "Productivity & Habits",
    "time management": "Productivity & Habits",
    "attention": "Productivity & Habits",
    "execution": "Productivity & Habits",
    "work-life balance": "Productivity & Habits",
    # Business & Leadership
    "business": "Business & Leadership",
    "leadership": "Business & Leadership",
    "management": "Business & Leadership",
    "strategy": "Business & Leadership",
    "entrepreneurship": "Business & Leadership",
    "startups": "Business & Leadership",
    "corporate management": "Business & Leadership",
    "organizational culture": "Business & Leadership",
    "organizational design": "Business & Leadership",
    "organizational health": "Business & Leadership",
    "management systems": "Business & Leadership",
    "project management": "Business & Leadership",
    "sales": "Business & Leadership",
    "pitching": "Business & Leadership",
    "small business": "Business & Leadership",
    "teamwork": "Business & Leadership",
    "performance": "Business & Leadership",
    "collaboration": "Business & Leadership",
    "case studies": "Business & Leadership",
    "steve jobs": "Business & Leadership",
    "reliability": "Business & Leadership",
    "professional development": "Business & Leadership",
    "career": "Business & Leadership",
    # Finance & Wealth
    "finance": "Finance & Wealth", "investing": "Finance & Wealth",
    "personal finance": "Finance & Wealth",
    # Communication & Relationships
    "communication": "Communication & Relationships",
    "relationships": "Communication & Relationships",
    "persuasion": "Communication & Relationships",
    "public speaking": "Communication & Relationships",
    "presentation": "Communication & Relationships",
    "presentation design": "Communication & Relationships",
    "visual communication": "Communication & Relationships",
    "negotiation": "Communication & Relationships",
    "conflict resolution": "Communication & Relationships",
    "storytelling": "Communication & Relationships",
    "ted": "Communication & Relationships",
    # Creativity & Art
    "creativity": "Creativity & Art", "art": "Creativity & Art",
    "design": "Creativity & Art", "writing": "Creativity & Art",
    "music": "Creativity & Art",
    "creative nonfiction": "Creativity & Art",
    "aesthetics": "Creativity & Art",
    # Education & Learning
    "education": "Education & Learning",
    "critical thinking": "Education & Learning",
    "academic": "Education & Learning",
    "student success": "Education & Learning",
    "reference": "Education & Learning", "workbook": "Education & Learning",
    # Science & Technology
    "science": "Science & Technology",
    "popular science": "Science & Technology",
    "technology": "Science & Technology", "ai": "Science & Technology",
    "evolution": "Science & Technology",
    "microbiology": "Science & Technology",
    "environmental science": "Science & Technology",
    "futurism": "Science & Technology",
    "future of work": "Science & Technology",
    "media studies": "Science & Technology",
    # Memoir & Biography
    "memoir": "Memoir & Biography",
    "autobiography": "Memoir & Biography",
    "biography": "Memoir & Biography",
    # History & Classics
    "history": "History & Classics", "classics": "History & Classics",
    "asian history": "History & Classics",
    "korean history": "History & Classics",
    "cultural history": "History & Classics",
    "holocaust": "History & Classics",
    # Nature & Environment
    "nature writing": "Nature & Environment",
    "ecology": "Nature & Environment", "nature": "Nature & Environment",
    "conservation": "Nature & Environment",
    "conservation science": "Nature & Environment",
    "rewilding": "Nature & Environment",
    "shinrin-yoku": "Nature & Environment",
    "forestry": "Nature & Environment",
    "environment": "Nature & Environment",
    "environmental studies": "Nature & Environment",
    "environmental literature": "Nature & Environment",
    "nature observation": "Nature & Environment",
    "nature therapy": "Nature & Environment",
    "outdoor skills": "Nature & Environment",
    "navigation": "Nature & Environment",
    "mountaineering": "Nature & Environment",
    "horses": "Nature & Environment", "falconry": "Nature & Environment",
    # Travel & Adventure
    "travel": "Travel & Adventure", "expat life": "Travel & Adventure",
    "pilgrimage": "Travel & Adventure",
    "solo travel": "Travel & Adventure",
    "digital nomad": "Travel & Adventure",
    "american west": "Travel & Adventure",
    "walking": "Travel & Adventure",
    # Culture & Society
    "korean culture": "Culture & Society",
    "japanese culture": "Culture & Society",
    "chinese culture": "Culture & Society",
    "french culture": "Culture & Society",
    "sociology": "Culture & Society", "feminism": "Culture & Society",
    "gender": "Culture & Society", "gender studies": "Culture & Society",
    "women": "Culture & Society", "anthropology": "Culture & Society",
    "cultural studies": "Culture & Society",
    "cultural criticism": "Culture & Society",
    "cross-cultural": "Culture & Society", "culture": "Culture & Society",
    "social commentary": "Culture & Society",
    "social justice": "Culture & Society",
    "social science": "Culture & Society",
    "pop culture": "Culture & Society",
    "modern culture": "Culture & Society", "k-pop": "Culture & Society",
    "sexual assault": "Culture & Society",
    "motherhood": "Parenting & Family",
    # Parenting & Family
    "parenting": "Parenting & Family",
    "child development": "Parenting & Family",
    "family": "Parenting & Family", "marriage": "Parenting & Family",
    "infidelity": "Parenting & Family",
    # Happiness & Resilience
    "happiness": "Happiness & Resilience",
    "resilience": "Happiness & Resilience",
    "optimism": "Happiness & Resilience",
    "positive psychology": "Happiness & Resilience",
    "pleasure": "Happiness & Resilience",
    # Essays & Poetry
    "essays": "Essays & Poetry", "essay": "Essays & Poetry",
    "poetry": "Essays & Poetry", "anthology": "Essays & Poetry",
    "literature": "Essays & Poetry",
    "non-fiction": "Essays & Poetry",
    # Lifestyle & Minimalism
    "lifestyle": "Lifestyle & Minimalism",
    "minimalism": "Lifestyle & Minimalism",
    "slow living": "Lifestyle & Minimalism", "home": "Lifestyle & Minimalism",
    "rest": "Lifestyle & Minimalism", "tea": "Lifestyle & Minimalism",
    "daily reader": "Lifestyle & Minimalism",
    # Fiction & Literature
    "fiction": "Fiction & Literature", "novel": "Fiction & Literature",
    "classical literature": "Fiction & Literature",
    "japanese literature": "Fiction & Literature",
    "indian literature": "Fiction & Literature",
    "american literature": "Fiction & Literature",
    "scottish literature": "Fiction & Literature",
    "african literature": "Fiction & Literature",
    "literary history": "Fiction & Literature",
    "contemporary": "Fiction & Literature",
    # Fantasy & Sci-Fi
    "fantasy": "Fantasy & Sci-Fi", "speculative": "Fantasy & Sci-Fi",
    # Mystery & Thriller
    "true crime": "Mystery & Thriller",
    "investigative": "Mystery & Thriller",
    "investigative journalism": "Mystery & Thriller",
    # Tales & Fables
    "philosophical fiction": "Tales & Fables",
}


def canonicalize(raw_tags):
    """Map raw tags to canonical list, preserving first-seen order, max 3."""
    seen = []
    for raw in raw_tags or []:
        if not isinstance(raw, str):
            continue
        key = raw.strip().casefold()
        if key == "feature":
            continue  # handled via `features`, never a category
        mapped = TAG_MAP.get(key)
        if mapped is None:
            continue  # app-side Others; logged by caller
        if mapped not in seen:
            seen.append(mapped)
        if len(seen) == 3:
            break
    return seen


def main():
    data = json.loads(MANIFEST.read_text())
    books = data.get("books", [])

    # Dedupe by id (keep last occurrence), drop `feature`, map tags.
    by_id = {}
    order = []
    featured = []
    unmapped = {}
    for book in books:
        bid = book.get("id", "")
        raw_tags = list(book.get("tags", []))
        if any(isinstance(t, str) and t.strip().casefold() == "feature" for t in raw_tags):
            if bid and bid not in featured:
                featured.append(bid)
        new_tags = canonicalize(raw_tags)
        for raw in raw_tags:
            if isinstance(raw, str) and raw.strip().casefold() != "feature":
                if raw.strip().casefold() not in TAG_MAP:
                    unmapped.setdefault(raw.strip(), []).append(bid)
        cleaned = dict(book)
        cleaned["tags"] = new_tags
        if bid not in by_id:
            order.append(bid)
        by_id[bid] = cleaned  # last wins

    books_out = [by_id[bid] for bid in order]
    others_count = sum(1 for b in books_out if not b.get("tags"))

    data_out = {
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "tags": CANONICAL_TAGS,
        "features": featured,
        "books": books_out,
    }
    MANIFEST.write_text(json.dumps(data_out, indent=2, ensure_ascii=False) + "\n")

    print(f"books in: {len(books)} -> out: {len(books_out)}")
    print(f"canonical tags: {len(CANONICAL_TAGS)} (Others app-only, not stored)")
    print(f"featured ids: {len(featured)}")
    print(f"books with [] tags (app Others): {others_count}")
    if unmapped:
        print(f"unmapped raw tags ({len(unmapped)}), all fall back to app Others:")
        for tag in sorted(unmapped):
            print(f"  {tag!r}: {len(unmapped[tag])} book(s)")


if __name__ == "__main__":
    sys.exit(main())
