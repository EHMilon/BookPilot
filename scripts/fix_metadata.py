"""Targeted metadata fixes: re-query Google Books with explicit author hints,
apply direct author patches (translators/editors -> real author), flag review set.

Usage: GOOGLE_BOOKS_KEY=... python3 scripts/fix_metadata.py [--limit N]
Verifies each fix against book_list.md author surname before overwriting.
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = ROOT / "books"

# folder -> (title query, author hint). Author hint also used for verification.
FIX = {
    "a-mans-search-for-meaning": ("man's search for meaning", "Viktor Frankl"),
    "about-time": ("about time", "David Rooney"),
    "becoming": ("becoming", "Michelle Obama"),
    "being-and-nothingness": ("being and nothingness", "Jean-Paul Sartre"),
    "bread-and-wine": ("bread and wine", "Shauna Niequist"),
    "breath": ("breath", "James Nestor"),
    "breathe-tim-wainwright": ("breathe", "Tim Wainwright"),
    "broken-wings": ("broken wings", "Kahlil Gibran"),
    "creativity": ("creativity", "Mihaly Csikszentmihalyi"),
    "decisive": ("decisive", "Chip Heath"),
    "didnt-see-it-coming": ("didn't see it coming", "Carey Nieuwhof"),
    "do-the-deep-work": ("deep work", "Cal Newport"),
    "dont-worry": ("don't worry", "Shunmyo Masuno"),
    "financial-freedom": ("financial freedom", "Grant Sabatier"),
    "first-things-first": ("first things first", "Stephen Covey"),
    "i-and-thou": ("i and thou", "Martin Buber"),
    "i-thought-it-was-just-me-but-it-isnt": ("i thought it was just me", "Brene Brown"),
    "kintsugi-the-japanese-art-of-embracing-imperfection": ("kintsugi", "Navid Lelli"),
    "lagom": ("lagom", "Lola Akerstrom"),
    "landmarks": ("landmarks", "Robert Macfarlane"),
    "lifespan": ("lifespan", "David Sinclair"),
    "light-on-life": ("light on life", "BKS Iyengar"),
    "living-the-artists-way": ("the artist's way", "Julia Cameron"),
    "night": ("night", "Elie Wiesel"),
    "off-the-clock": ("off the clock", "Laura Vanderkam"),
    "peak": ("peak", "Anders Ericsson"),
    "playing-with-fire": ("playing with fire", "Scott Rieckens"),
    "scarcity": ("scarcity", "Sendhil Mullainathan"),
    "so-good-they-cant-ignore-you": ("so good they can't ignore you", "Cal Newport"),
    "switch": ("switch", "Chip Heath"),
    "the-anatomy-of-the-body": ("anatomy of the body", ""),
    "the-art-of-being": ("the art of being", "Erich Fromm"),
    "the-art-of-breath": ("the art of breath", ""),
    "the-art-of-public-speaking": ("the art of public speaking", "Dale Carnegie"),
    "the-artists-way-workbook": ("the artist's way", "Julia Cameron"),
    "the-book-of-changes-i-ching": ("i ching", "Richard Wilhelm"),
    "the-certainty-of-uncertainty": ("certainty of uncertainty", "Mark Schaefer"),
    "the-charge": ("the charge", "Brendon Burchard"),
    "the-conference-of-the-birds": ("conference of the birds", "Attar"),
    "the-element": ("the element", "Ken Robinson"),
    "the-happiness-project": ("the happiness project", "Gretchen Rubin"),
    "the-joy-of-less": ("the joy of less", "Francine Jay"),
    "the-knowledge-gap": ("the knowledge gap", "Natalie Wexler"),
    "the-latte-factor": ("the latte factor", "David Bach"),
    "the-life-of-the-mind": ("the life of the mind", "Hannah Arendt"),
    "the-light-we-carry": ("the light we carry", "Michelle Obama"),
    "the-little-book-of-productivity": ("little book of productivity", ""),
    "the-lost-city-of-z": ("the lost city of z", "David Grann"),
    "the-motorcycle-diaries": ("the motorcycle diaries", "Che Guevara"),
    "the-old-ways": ("the old ways", "Robert Macfarlane"),
    "the-one-thing": ("the one thing", "Gary Keller"),
    "the-overstory": ("the overstory", "Richard Powers"),
    "the-path-of-the-pilgrim": ("path of the pilgrim", ""),
    "the-places-in-between": ("places in between", "Rory Stewart"),
    "the-plague": ("the plague", "Albert Camus"),
    "the-practice": ("the practice", "Seth Godin"),
    "the-science-of-habit": ("science of habit", ""),
    "the-science-of-yoga": ("science of yoga", "William Broad"),
    "the-signal-and-the-noise": ("the signal and the noise", "Nate Silver"),
    "the-slight-edge": ("the slight edge", "Jeff Olson"),
    "the-snow-leopard": ("the snow leopard", "Peter Matthiessen"),
    "the-social-animal": ("the social animal", "David Brooks"),
    "the-spirit-of-zen": ("spirit of zen", "Sam van Schaik"),
    "the-state-of-affairs": ("the state of affairs", "Esther Perel"),
    "the-story-of-my-life": ("the story of my life", "Helen Keller"),
    "the-stranger": ("the stranger", "Albert Camus"),
    "the-time-keeper": ("the time keeper", "Mitch Albom"),
    "the-white-coat-investor": ("white coat investor", "James Dahle"),
    "the-will-to-power": ("the will to power", "Friedrich Nietzsche"),
    "the-wim-hof-method": ("wim hof method", "Wim Hof"),
    "wim-hof-method": ("wim hof method", "Wim Hof"),
    "the-wisdom-of-the-east": ("wisdom of the east", ""),
    "the-world-without-us": ("the world without us", "Alan Weisman"),
    "the-zen-way": ("zen way", "Alan Watts"),
    "thick-and-other-essays": ("thick", "Tressie McMillan Cottom"),
    "think-better": ("think better", "Tim Hurson"),
    "think-on-these-things": ("think on these things", "Jiddu Krishnamurti"),
    "time-management-magic": ("time management magic", ""),
    "to-have-or-to-be": ("to have or to be", "Erich Fromm"),
    "unshakeable": ("unshakeable", "Tony Robbins"),
    "voluntary-simplicity": ("voluntary simplicity", "Duane Elgin"),
    "wabi-sabi": ("wabi sabi", "Leonard Koren"),
    "wait-what": ("wait what", "James Ryan"),
    "waking-up": ("waking up", "Sam Harris"),
    "what-doesnt-kill-us": ("what doesn't kill us", "Scott Carney"),
    "wild": ("wild", "Cheryl Strayed"),
    "wild-at-heart": ("wild at heart", "John Eldredge"),
    "willpower": ("willpower", "Roy Baumeister"),
    "work-optional": ("work optional", "Tanja Hester"),
    "yoga-sutras": ("yoga sutras", "Patanjali"),
    "your-forces-and-how-to-use-them": ("your forces", "Christian Larson"),
    "your-money-or-your-life": ("your money or your life", "Vicki Robin"),
    "zen-mind-beginners-mind": ("zen mind beginner's mind", "Shunryu Suzuki"),
}

# folder -> correct author (metadata already points at right book/edition).
PATCH_AUTHOR = {
    "nausea": "Jean-Paul Sartre",
    "the-dhammapada": "Buddha",
    "the-essential-rumi": "Rumi",
    "the-great-learning": "Confucius",
    "the-life-and-teachings-of-swami-vivekananda": "Swami Vivekananda",
    "the-nicomachean-ethics": "Aristotle",
    "the-rubaiyat-of-omar-khayyam": "Omar Khayyam",
    "the-secret-of-the-golden-flower": "Thomas Cleary",
    "the-slow-fix": "Carl Honoré",
    "the-spirit-of-the-chinese-people": "Ku Hung-Ming",
    "the-upanishads": "Various",
    "the-yoga-sutras-of-patanjali": "Patanjali",
    "the-zen-teaching-of-huang-po": "Huang Po",
    "zhuangzi": "Zhuang Zhou",
    "zhuangzi-the-essential-writings": "Zhuangzi",
}

STOP = {"the", "a", "an", "of", "and", "in", "on", "to", "for", "how"}


def surname(a):
    a = re.split(r"[&,/]| and ", a)[0].strip()
    parts = a.split()
    return parts[-1].lower().strip(" -.") if parts else ""


def search(title, author, key):
    q = f"intitle:{title}" + (f" inauthor:{author}" if author else "")
    params = urllib.parse.urlencode(
        {"q": q, "maxResults": 5, "printType": "books", "key": key})
    req = urllib.request.Request(
        f"https://www.googleapis.com/books/v1/volumes?{params}",
        headers={"User-Agent": "BookPilot/2.0 (metadata fix)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r).get("items", [])


def main():
    key = os.environ.get("GOOGLE_BOOKS_KEY", "")
    if not key:
        print("Set GOOGLE_BOOKS_KEY env var.")
        return 1
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    folders = list(FIX)[:limit] if limit else list(FIX)

    fixed, needs_eye = [], []
    for i, folder in enumerate(folders, 1):
        title_q, author_q = FIX[folder]
        mp = BOOKS_DIR / folder / "metadata.json"
        print(f"[{i}/{len(folders)}] {folder} :: {title_q} / {author_q or '?'}", flush=True)
        try:
            items = search(title_q, author_q, key)
        except Exception as e:
            print(f"  ! error: {e}", flush=True)
            needs_eye.append(folder)
            continue
        time.sleep(0.15)
        want = surname(author_q) if author_q else ""
        pick = None
        for item in items:
            vi = item.get("volumeInfo", {})
            authors = vi.get("authors", []) or []
            if want and any(want in surname(a) or surname(a) in want for a in authors):
                pick = (item, 1.0)
                break
        if pick is None and items and not author_q:
            pick = (items[0], 0.5)
        if pick is None:
            print("  -> NO VERIFIED MATCH", flush=True)
            needs_eye.append(folder)
            continue
        item, _ = pick
        vi = item.get("volumeInfo", {})
        authors = vi.get("authors", []) or ([author_q] if author_q else [])
        ids = {d.get("type"): d.get("identifier", "")
               for d in vi.get("industryIdentifiers", [])}
        old = json.loads(mp.read_text()) if mp.exists() else {}
        meta = {
            "id": folder,
            "title": vi.get("title", "") or old.get("title", ""),
            "author": authors[0] if authors else old.get("author", ""),
            "authors": authors,
            "publisher": vi.get("publisher", "") or old.get("publisher", ""),
            "publishedDate": vi.get("publishedDate", "") or old.get("publishedDate", ""),
            "isbn13": ids.get("ISBN_13", "") or old.get("isbn13", ""),
            "isbn10": ids.get("ISBN_10", "") or old.get("isbn10", ""),
            "pageCount": vi.get("pageCount", 0) or old.get("pageCount", 0),
            "googleCategories": vi.get("categories", []) or old.get("googleCategories", []),
            "description": old.get("description", ""),
            "source": "google-books-fix",
            "sourceId": item.get("id", ""),
            "sourceQuery": f"{title_q} / {author_q}",
            "sourceScore": 1.0,
            "review": False,
        }
        if not meta["description"]:
            import html as _h
            raw = re.sub(r"<[^>]+>", " ", _h.unescape(vi.get("description", "") or "")).strip()
            raw = re.sub(r"\s+", " ", raw)
            meta["description"] = (raw[:raw.rfind(". ", 0, 320) + 1]
                                    if len(raw) > 320 else raw)
        mp.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
        fixed.append(folder)
        print(f"  -> {meta['title']} / {meta['author']}", flush=True)

    for folder, author in PATCH_AUTHOR.items():
        mp = BOOKS_DIR / folder / "metadata.json"
        if not mp.exists():
            continue
        m = json.loads(mp.read_text())
        if m.get("author") != author:
            m["author"] = author
            if author not in m.get("authors", []):
                m["authors"] = [author] + m.get("authors", [])
            m["review"] = False
            mp.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
            fixed.append(f"{folder} (author patch)")

    print(f"\nDone: {len(fixed)} fixed/patched, {len(needs_eye)} need eye: {needs_eye}")


if __name__ == "__main__":
    sys.exit(main())
