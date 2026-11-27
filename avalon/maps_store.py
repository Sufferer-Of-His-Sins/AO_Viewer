from avalon.libs import *


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
    query = query.strip().lower()
    if not query:
        return list(maps)

    filtered = []
    for m in maps:
        name = m["name"].lower()
        if query in name or name.startswith(query):
            filtered.append(m)
            continue
        it = iter(name)
        if all(c in it for c in query):
            filtered.append(m)
    return filtered


def find_by_name(maps: list, name: str):
    name_clean = name.strip().lower().replace(" ", "")
    for m in maps:
        if m["name"].lower().replace(" ", "") == name_clean:
            return m
    for m in maps:
        if name_clean in m["name"].lower().replace(" ", ""):
            return m
    return None


def _letters(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalpha())


def best_match(maps: list, ocr_text):
    if isinstance(ocr_text, str):
        candidates = [ocr_text]
    else:
        candidates = [item for item in ocr_text if item]
    if not candidates:
        return None

    names = [(m, _letters(m["name"])) for m in maps]
    scores = {}
    for cand in candidates:
        query = _letters(cand)
        if len(query) < 6:
            continue
        for m, name in names:
            if not name:
                continue
            if query == name:
                return m
            ratio = SequenceMatcher(None, query, name).ratio()
            prev = scores.get(m["name"])
            if prev is None or ratio > prev[0]:
                scores[m["name"]] = (ratio, m)

    if not scores:
        return None

    ranked = sorted(scores.values(), key=lambda item: -item[0])
    best_ratio, best_map = ranked[0]
    second = ranked[1][0] if len(ranked) > 1 else 0.0
    if best_ratio < 0.88:
        return None
    if second >= 0.84 and best_ratio - second < 0.045:
        return None
    return best_map


def first_search_hit(maps: list, query: str):
    query = query.strip().lower()
    if not query:
        return None
    for m in maps:
        if query in m["name"].lower() or m["name"].lower().startswith(query):
            return m
    return None