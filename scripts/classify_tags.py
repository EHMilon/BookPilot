"""Classify tags for books with empty tags[] using metadata signals.

Zero-cost pass: googleCategories + title/author/description keywords +
head of summary.md (local scan, zero tokens). No LLM, no API calls.
Dry-run default; --write applies to manifest.

Usage: python3 scripts/classify_tags.py [--write] [--ids a,b,c]
Writes scripts/classify_report.json with per-book tags + confidence.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "book_manifest.json"
BOOKS_DIR = ROOT / "books"
REPORT = Path(__file__).resolve().parent / "classify_report.json"

CAT_MAP = [
    ("business", "Business & Leadership"), ("economics", "Business & Leadership"),
    ("management", "Business & Leadership"), ("leadership", "Business & Leadership"),
    ("personal finance", "Finance & Wealth"), ("finance", "Finance & Wealth"),
    ("invest", "Finance & Wealth"), ("wealth", "Finance & Wealth"),
    ("self-help", "Self-Help"), ("self help", "Self-Help"),
    ("psychology", "Psychology"),
    ("philosophy", "Philosophy"),
    ("religion", "Mindfulness & Spirituality"), ("spiritual", "Mindfulness & Spirituality"),
    ("body, mind & spirit", "Mindfulness & Spirituality"), ("body mind spirit", "Mindfulness & Spirituality"),
    ("meditation", "Mindfulness & Spirituality"), ("mindfulness", "Mindfulness & Spirituality"),
    ("buddhism", "Mindfulness & Spirituality"), ("yoga", "Mindfulness & Spirituality"),
    ("hinduism", "Mindfulness & Spirituality"), ("taoism", "Mindfulness & Spirituality"),
    ("neuroscience", "Neuroscience & Brain"), ("cognitive", "Neuroscience & Brain"),
    ("health", "Health & Nutrition"), ("fitness", "Health & Nutrition"),
    ("medical", "Health & Nutrition"), ("nutrition", "Health & Nutrition"),
    ("cooking", "Health & Nutrition"), ("diet", "Health & Nutrition"),
    ("mental health", "Mental Health & Wellbeing"),
    ("family & relationships", "Communication & Relationships"),
    ("marriage", "Communication & Relationships"), ("interpersonal", "Communication & Relationships"),
    ("parent", "Parenting & Family"), ("child", "Parenting & Family"),
    ("biography", "Memoir & Biography"), ("autobiography", "Memoir & Biography"),
    ("memoir", "Memoir & Biography"),
    ("history", "History & Classics"), ("classics", "History & Classics"),
    ("ancient", "History & Classics"),
    ("fiction", "Fiction & Literature"), ("literary", "Fiction & Literature"),
    ("poetry", "Essays & Poetry"), ("essays", "Essays & Poetry"),
    ("science", "Science & Technology"), ("technology", "Science & Technology"),
    ("nature", "Nature & Environment"), ("environment", "Nature & Environment"),
    ("animals", "Nature & Environment"), ("ecology", "Nature & Environment"),
    ("travel", "Travel & Adventure"), ("adventure", "Travel & Adventure"),
    ("art", "Creativity & Art"), ("design", "Creativity & Art"),
    ("photography", "Creativity & Art"), ("creativity", "Creativity & Art"),
    ("music", "Creativity & Art"),
    ("education", "Education & Learning"), ("study", "Education & Learning"),
    ("reference", "Education & Learning"), ("language", "Education & Learning"),
    ("social science", "Culture & Society"), ("sociology", "Culture & Society"),
    ("political", "Culture & Society"), ("anthropology", "Culture & Society"),
    ("true crime", "Mystery & Thriller"), ("mystery", "Mystery & Thriller"),
    ("detective", "Mystery & Thriller"), ("thriller", "Mystery & Thriller"),
    ("fantasy", "Fantasy & Sci-Fi"), ("science fiction", "Fantasy & Sci-Fi"),
    ("fairy tales", "Tales & Fables"), ("folklore", "Tales & Fables"),
    ("fables", "Tales & Fables"), ("mythology", "Tales & Fables"),
    ("juvenile", "Parenting & Family"), ("parenting", "Parenting & Family"),
]

TERMS = {
    "Self-Help": ["success", "confidence", "self-esteem", "potential", "greatness", "mindset", "grit", "persever", "excellence", "winner", "champion", "mastery", "genius", "limitless", "dream", "desire", "belief", "miracle morning", "unstoppable", "achieve", "ambition"],
    "Productivity & Habits": ["habit", "procrastinat", "productiv", "focus", "discipline", "willpower", "routine", "goal", "priorit", "execution", "distract", "attention", "time management", "deep work", "getting things done", "action", "lazy", "delay", "eating frog", "one thing", "compound effect"],
    "Psychology": ["psycholog", "bias", "behavioral", "nudge", "emotion", "personality", "intelligence", "irrational", "freud", "jung", "maslow", "milgram", "mental model", "heuristic", "manipulat", "thinking", "mind ", "cognition", "intuition", "judgment", "unconscious", "thin-slic", "first impression", "blink", "snap decision"],
    "Philosophy": ["stoic", "seneca", "marcus", "epictetus", "tao", "zen", "buddha", "confucius", "plato", "aristotle", "nietzsche", "sartre", "kant", "schopenhauer", "existential", "virtue", "ethics", "analects", "dhammapada", "meditations"],
    "Neuroscience & Brain": ["brain", "neuro", "dopamine", "memory", "cortex", "amygdala", "subconscious", "deliberate practice", "talent", "flow"],
    "Business & Leadership": ["startup", "entrepreneur", "market", "sales", "negotiat", "investor", "business", "ceo", "founder", "company", "corporate", "trade", "commerce", "management", "leader", "executive", "capitalism", "monopoly", "scaling", "courage", "dare", "vulnerability at work", "brave", "strategy", "tactics"],
    "Finance & Wealth": ["money", "invest", "financ", "debt", "retire", "budget", "frugal", "millionaire", "wealth", "rich", "poor", "dollar", "income", "real estate", "stock market", "salary", "compound interest"],
    "Mental Health & Wellbeing": ["anxiety", "depress", "therapy", "trauma", "healing", "burnout", "vulnerab", "shame", "grief", "addict", "wound", "trigger", "sadness", "lonel", "counsel"],
    "Happiness & Resilience": ["happiness", "happier", "happy", "joy", "gratitud", "optimism", "flourish", "wellbeing", "well-being", "contentment", "bliss", "cheerful", "delight", "satisfaction", "resilien", "antifragile", "fragil", "black swan", "uncertain", "risk", "volatil", "disorder", "randomness"],
    "Mindfulness & Spirituality": ["meditat", "mindful", "spiritual", "awaken", "enlighten", "prayer", "soul", "sacred", "divine", "gita", "sutra", "vedanta", "buddhis", "hindu", "yogi", "guru", "monk", "contemplat", "surrender", "faith", "bible", "rumi", "sufi", "mystic", "transcend", "stillness", "presence", "inner peace", "upanishad"],
    "Health & Nutrition": ["diet", "nutrition", "fasting", "keto", "yoga", "breath", "sleep", "exercise", "fitness", "gut", "hormone", "longevity", "immune", "vegan", "body", "disease", "doctor", "medicine", "heal", "pain", "weight", "obes", "diabet", "cancer", "heart", "muscle", "food", "sugar", "ayurveda", "pranayama", "running", "walking"],
    "Communication & Relationships": ["marriage", "dating", "relationship", "love", "attach", "communication", "conversation", "influence", "persua", "empathy", "listen", "trust", "intimacy", "divorce", "romance", "compassion", "kindness", "friendship"],
    "Parenting & Family": ["parent", "childhood", "mother", "father", "family", "raising", "toddler", "teen", "kids", "baby", "daughter", "son", "motherhood"],
    "Memoir & Biography": ["memoir", "autobiography", "my life", "growing up", "biography", "life of", "my story", "nobel"],
    "History & Classics": ["history", "ancient", "empire", "civilization", "century", "rome", "samurai", "bushido", "revolution", "holocaust", "dynasty", "renaissance", "shogun", "cold war", "middle ages", "classical", "sapiens", "humankind", "homo ", "civilisation", "war", "battle", "warfare", "conquest"],
    "Creativity & Art": ["creativ", "artist", "design", "writing", "photograph", "innovat", "paint", "music", "dance", "film", "novel", "author", "craft", "draw"],
    "Education & Learning": ["learn", "study", "school", "student", "teach", "reading", "education", "knowledge", "literacy", "skill", "curriculum", "ignorance", "ultralearn", "exam"],
    "Science & Technology": ["physics", "quantum", "evolution", "cosmos", "universe", "biolog", "genome", "climate", "mathematic", "science", "scientist", "darwin", "einstein", "experiment", "dna", "gene", "species", "technology", "computer", "algorithm"],
    "Nature & Environment": ["ocean", "forest", "wilderness", "wild", "nature", "animal", "earth", "garden", "mountain", "river", "tree", "bird", "jungle", "desert", "snow", "trail", "ecolog", "sustainab", "wolf", "whale", "planet"],
    "Travel & Adventure": ["travel", "journey", "adventure", "road", "voyage", "expedition", "pilgrim", "nomad", "wander", "odyssey", "tourist", "sailing", "hiking", "trekking", "charley", "walk across", "solitary"],
    "Culture & Society": ["culture", "society", "tribe", "inequal", "race", "gender", "feminis", "power", "class", "community", "justice", "oppress", "colonial", "freedom", "rights", "protest", "swed", "denmark", "norway", "finland", "japan", "china", "india", "africa"],
    "Essays & Poetry": ["essay", "poem", "poetry", "letters", "journal", "aphorism", "verse", "haiku", "anthology", "collection of"],
    "Lifestyle & Minimalism": ["minimal", "simple living", "declutter", "tidy", "lagom", "hygge", "wabi", "downshift", "voluntary simplicity", "enough", "essentialism", "frugal", "slow living", "less", "simple life", "unclutter"],
    "Fiction & Literature": ["novel", "stories", "short stor", "tale", "fable", "myth", "folklore", "fiction", "storytell", "allegory", "parable", "fairy", "narrative", "heaven", "afterlife", "protagonist", "novella"],
    "Mystery & Thriller": ["mystery", "murder", "crime", "detective", "thriller", "suspense", "killing", "serial killer", "cold case"],
    "Fantasy & Sci-Fi": ["fantasy", "science fiction", "sci-fi", "scifi", "space", "dragon", "magic", "dystopia", "alien", "robot", "galaxy", "wizard", "dune", "hobbit"],
    "Tales & Fables": ["aesop", "panchatantra", "jataka", "folk tale", "fairy tale", "fables", "kalila", " Arabian nights", "1001 nights"],
}

SUMMARY_CHARS = 3000


def classify(meta, folder=""):
    cats = [c.lower() for c in (meta.get("googleCategories") or [])]
    head = " ".join([meta.get("title", ""), meta.get("author", "")]).lower()
    body = (meta.get("description", "") or "").lower()
    if folder:
        sp = BOOKS_DIR / folder / "summary.md"
        if sp.exists():
            try:
                body += " " + sp.read_text(encoding="utf-8",
                                           errors="ignore")[:SUMMARY_CHARS].lower()
            except OSError:
                pass
    scores = {}
    for frag, tag in CAT_MAP:
        if any(frag in c for c in cats):
            scores[tag] = scores.get(tag, 0) + 3
    for tag, terms in TERMS.items():
        for t in terms:
            if t in head:
                scores[tag] = scores.get(tag, 0) + 2
            elif t in body:
                scores[tag] = scores.get(tag, 0) + 1
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    if not ranked:
        return ["Self-Help"], 0.2
    top = ranked[0][1]
    picks = [t for t, s in ranked if s >= max(3, top - top // 2)][:3]
    return picks, round(min(1.0, top / 8.0), 2)


def main():
    write = "--write" in sys.argv
    only = None
    if "--ids" in sys.argv:
        only = set(sys.argv[sys.argv.index("--ids") + 1].split(","))
    m = json.loads(MANIFEST.read_text())
    allowed = set(m["tags"])
    report = []
    for b in m["books"]:
        if b.get("tags"):
            continue
        if only and b["id"] not in only:
            continue
        mp = BOOKS_DIR / b["id"] / "metadata.json"
        meta = json.loads(mp.read_text()) if mp.exists() else {}
        tags, conf = classify(meta, b["id"])
        tags = [t for t in tags if t in allowed]
        rec = {"id": b["id"], "title": b.get("title", ""), "tags": tags,
               "confidence": conf, "review": conf < 0.5}
        report.append(rec)
        if write:
            b["tags"] = tags or []
            b["updatedAt"] = "2026-10-30"
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    low = [r for r in report if r["review"]]
    print(f"classified: {len(report)}, low-confidence (<0.5): {len(low)}, "
          f"{'APPLIED' if write else 'dry-run'}")
    if write:
        MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    else:
        print(Counter(t for r in report for t in r["tags"]).most_common())
        print("low-conf sample:", [r["id"] for r in low[:20]])


if __name__ == "__main__":
    sys.exit(main())
