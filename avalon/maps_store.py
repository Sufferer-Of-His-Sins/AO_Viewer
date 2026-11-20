from difflib import SequenceMatcher

from avalon.libs import *


def normalize(text: str) -> str:
    return text.lower().replace(" ", "").replace("-", "")


def match_score(name: str, query: str):
    n = normalize(name)
    q = normalize(query)
    if not q:
        return 0

    if n.startswith(q):
        return 0

    words = name.lower().replace("-", " ").split()
    if any(w.startswith(q) for w in words):
        return 1

    if q in n:
        return 2

    if len(q) >= 4:
        ratio = SequenceMatcher(None, q, n[:len(q)]).ratio()
        if ratio >= 0.8:
            return 3

    return None


def load_maps() -> list:
    path = DATA_DIR / "maps.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            maps = json.load(f)
    else:
        maps = []
    maps.sort(key=lambda m: m["name"].lower())
    return maps


def filter_maps(maps: list, query: str) -> list:
    if not query.strip():
        return list(maps)

    found = []
    for m in maps:
        score = match_score(m["name"], query)
        if score is not None:
            found.append((score, m["name"].lower(), m))

    found.sort(key=lambda item: (item[0], item[1]))
    return [m for _, _, m in found]


def find_by_name(maps: list, name: str):
    name_clean = name.strip().lower().replace(" ", "")
    for m in maps:
        if m["name"].lower().replace(" ", "") == name_clean:
            return m
    for m in maps:
        if name_clean in m["name"].lower().replace(" ", ""):
            return m
    return None


def best_match(maps: list, ocr_text: str):
    ocr = ocr_text.lower().replace(" ", "").replace("-", "")
    best = None
    best_score = 0.0

    for m in maps:
        name = m["name"].lower().replace(" ", "").replace("-", "")
        if ocr == name:
            return m
        if ocr in name or name in ocr:
            score = min(len(ocr), len(name)) / max(len(ocr), len(name), 1)
            if score > best_score:
                best_score = score
                best = m
        else:
            common = sum(1 for a, b in zip(ocr, name) if a == b)
            score = common / max(len(ocr), len(name), 1)
            if score > best_score and score > 0.55:
                best_score = score
                best = m

    return best if best_score > 0.5 else None


def first_search_hit(maps: list, query: str):
    if not query.strip():
        return None
    found = filter_maps(maps, query)
    return found[0] if found else None