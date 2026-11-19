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
    query = query.strip().lower()
    if not query:
        return None
    for m in maps:
        if query in m["name"].lower() or m["name"].lower().startswith(query):
            return m
    return None