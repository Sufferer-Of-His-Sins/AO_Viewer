from avalon.libs import *

def _compact(text: str) -> str:
    return re.sub(r"[^A-Za-z]", "", text or "").upper()


def _is_mark(text: str) -> bool:
    word = _compact(text)
    if len(word) < 5:
        return False
    return "AVALON" in word or "TRAVELER" in word


def _cover(img: Image.Image, x, y, w, h) -> Image.Image:
    pad = 4
    x = max(0, x - pad)
    y = max(0, y - pad)
    w = min(img.width - x, w + pad * 2)
    h = min(img.height - y, h + pad * 2)
    if w < 4 or h < 4 or y < 1 or y + h >= img.height - 1:
        return img
    if w > img.width * 0.85 or h > img.height * 0.45:
        return img

    img = img.copy()
    px = img.load()
    for yy in range(y, y + h):
        t = (yy - y + 1) / (h + 1)
        for xx in range(x, x + w):
            top = px[xx, y - 1]
            bot = px[xx, y + h]
            px[xx, yy] = tuple(int(a * (1 - t) + b * t) for a, b in zip(top, bot))
    return img


def strip_watermark(img: Image.Image) -> Image.Image:
    try:
        import pytesseract
        from pytesseract import Output
    except Exception:
        return img

    scale = 1.0
    small = img
    if img.width > 1400:
        scale = 1400 / img.width
        small = img.resize(
            (1400, max(1, int(img.height * scale))),
            Image.Resampling.BILINEAR,
        )

    try:
        data = pytesseract.image_to_data(
            small,
            output_type=Output.DICT,
            config="--psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        )
    except Exception:
        return img

    lines = {}
    for i, raw in enumerate(data.get("text", [])):
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(i)

    boxes = []
    for idxs in lines.values():
        joined = "".join(data["text"][i] or "" for i in idxs)
        if not _is_mark(joined):
            continue
        xs, ys, xe, ye = [], [], [], []
        for i in idxs:
            w, h = data["width"][i], data["height"][i]
            if w <= 0 or h <= 0:
                continue
            x, y = data["left"][i], data["top"][i]
            xs.append(x)
            ys.append(y)
            xe.append(x + w)
            ye.append(y + h)
        if xs:
            boxes.append((min(xs), min(ys), max(xe), max(ye)))

    if not boxes:
        return img

    x1 = min(b[0] for b in boxes)
    y1 = min(b[1] for b in boxes)
    x2 = max(b[2] for b in boxes)
    y2 = max(b[3] for b in boxes)
    inv = 1 / scale
    return _cover(
        img,
        int(x1 * inv),
        int(y1 * inv),
        int((x2 - x1) * inv),
        int((y2 - y1) * inv),
    )
