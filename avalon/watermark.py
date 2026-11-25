import base64
import os
import re
import sys

import numpy as np
from PIL import Image, ImageOps

try:
    import cv2
except Exception:
    cv2 = None

WORDS = ("AVALON", "TRAVELER")

# Шаблон знака AVALON TRAVELERS (маска тонких светлых штрихов, PNG в base64).
# Шаблон усреднён по нескольким скриншотам. Размер знака немного плавает
# (масштаб 0.9-1.1), поэтому ищем его в нескольких масштабах.
TEMPLATE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAIwAAAA7CAAAAACMZD0vAAADTUlEQVRoBc3BAW7jiAFFMb77H/pXsmQnM3azQAu0IfOL5BfJDyb/S/lF8ovkF8kvkl8kX5b/r/wi+UXyl+U2uS0vk8vI08gf5k1uk3f5d0YuI7eRy8jTyDdzyDdDLpN3YfJuyGVyG7kMuY18GfnbyMPkXQ6TN0MuI5eRy5DbyMvIbfIw5GHyLoflzWS5TS6Ty2hyGXmZvExO0+Q0eZfPRiaXycPIw9DkMvI08jI5TSaHybt8NjHyMHKaXCYml5GnyTeTw2SEybt8NGLkMjmMXCZMHkaeJt9MDhMTJu/y0eQwuYww8jA5jJxGnibfTA4TJibv8tHkNLlMjFwmp8lp5GnyzeQwOUws7/LJyGHkMjG5jBxGTiNPky+T0+QwsbzLB/Mll5HJZb7kNHkaeZmcJqfJ8i4fjFwmlznkMnKZnCYvk5fJafIwTd7ky3IZuYxchlxGLiOHyZfJbfIwuQx5ky/Lw8jT5DLkMnmavBs5DHmYXEbe5cvyMPI0uYzcJk/zl5zmltvkNnmX/978If+p/CL5RfKL5BfJL5KHeclhzSGfTJ7mTzlMbvNRbnPKQz5afjC5Td5MfracJqfllC/L0/KwfLLclneTn00Ok2/yZXlaHpYvy225TN4t/2Q5TL7Jl+VpuSxflsvkYflg8g+Ww+SbvIzc1vLdwnJbHpYPJj+bnJZvcpovYW65jdyWyWH+ksPkaT7LaR5yycvIZTKnPMwhy2GxHEbeTJ7msxxGc8opL5PbxDR5mEMuk+Uw8mbkR5PD5DQ55WVym7Asp6HFclgsRt5N/sFymFyWQ14mt8lh5DSXlsNiYfJu8g+Ww+SyHPIyuU1Ok9OIaXJYrLV8MPnZ5DDyTV4mt8lh5DRhshwmk+WDyY9GTkMOyyEvk9vEHHIYOUwTRpbPJk/zWU7z0HLKy+Q2GTGXHCbLYWJym1uY5hTzQV7mlIe8TG4Lk9vysNwWk08m38whL8tfloe8TG7LYbnMSy6T5aPJDyZ/Wh7yMrkth8lp5GFymSYfTX4y+cPIIS+T23KaHCa3yWXks8mPJoflMjnlZXJbTiNMbpPLyGeTny2nEUZO+bJcJg/zkJflMnmap5zmIcwl300e5pRLfpH8IvlF8ovkF/kX0ZiLS40y+YUAAAAASUVORK5CYII="

MATCH_THRESHOLD = 0.4   # ниже этой оценки знаком считаться не будет
_template = None


def _compact(text):
    return re.sub(r"[^A-Za-z]", "", text or "").upper()


def _is_mark(text):
    word = _compact(text)
    if len(word) < 5:
        return False
    return any(w in word for w in WORDS)


def _odd(n):
    n = int(n)
    return n if n % 2 == 1 else n + 1


def _cover(img, x, y, w, h):
    """Запасной вариант без OpenCV: вертикальный градиент между краями области."""
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


# ---------- поиск знака ----------

def _stroke_mask(arr, thr=18, smax=85):
    """Тонкие светлые малонасыщенные штрихи: именно так выглядит знак.
    Оранжевые дороги и порталы насыщенные, поэтому сюда не попадают."""
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    top = cv2.subtract(gray, cv2.medianBlur(gray, 9))
    sat = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)[:, :, 1]
    return (((top > thr) & (sat < smax)) * 255).astype(np.uint8)


def _blur(mask):
    return cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 1.0)


def _get_template():
    global _template
    if _template is None:
        raw = np.frombuffer(base64.b64decode(TEMPLATE_B64), np.uint8)
        _template = cv2.imdecode(raw, cv2.IMREAD_GRAYSCALE)
    return _template


def _match_scale(m, tpl, scale):
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    t = cv2.resize(tpl, None, fx=scale, fy=scale, interpolation=interp)
    if t.shape[0] < 8 or t.shape[0] >= m.shape[0] or t.shape[1] >= m.shape[1]:
        return 0.0, None
    tf = _blur(t)
    res = cv2.matchTemplate(m, tf, cv2.TM_CCOEFF_NORMED)
    # в пустых окнах корреляция даёт мусор, поэтому требуем достаточно штрихов
    win = cv2.matchTemplate(m, np.ones_like(tf), cv2.TM_CCORR)
    res[win < 0.5 * tf.sum()] = -1
    res = np.nan_to_num(res, nan=-1, posinf=-1, neginf=-1)
    _, score, _, loc = cv2.minMaxLoc(res)
    return float(score), (loc[0], loc[1], loc[0] + t.shape[1], loc[1] + t.shape[0])


def _find_region_template(arr):
    """Ищет знак по шаблону. Возвращает (оценка, (x1, y1, x2, y2))."""
    tpl = _get_template()
    m = _blur(_stroke_mask(arr))
    best = (0.0, None, 1.0)

    # грубый перебор масштабов, потом уточнение вокруг лучшего
    for s in np.arange(0.7, 1.51, 0.04):
        score, region = _match_scale(m, tpl, s)
        if score > best[0]:
            best = (score, region, s)
    centre = best[2]
    for s in np.arange(centre - 0.04, centre + 0.041, 0.01):
        score, region = _match_scale(m, tpl, s)
        if score > best[0]:
            best = (score, region, s)
    return best[0], best[1]


def _ocr_boxes(gray, scale):
    import pytesseract
    from pytesseract import Output

    data = pytesseract.image_to_data(
        gray,
        output_type=Output.DICT,
        config="--psm 11 -c tessedit_char_whitelist="
               "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    )

    lines = {}
    for i in range(len(data.get("text", []))):
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

    inv = 1 / scale
    return [tuple(int(v * inv) for v in b) for b in boxes]


def _find_region_ocr(img):
    """Запасной поиск через OCR (если шаблон не подошёл, например знак другого вида)."""
    try:
        import pytesseract  # noqa: F401
    except Exception:
        return None

    w0, h0 = img.size
    if w0 < 800:
        scale = min(4.0, 800 / w0)
    elif w0 > 1400:
        scale = 1400 / w0
    else:
        scale = 1.0

    big = img
    if scale != 1.0:
        big = img.resize(
            (max(1, int(w0 * scale)), max(1, int(h0 * scale))),
            Image.Resampling.LANCZOS,
        )
    gray = ImageOps.autocontrast(big.convert("L"))

    for variant in (gray, ImageOps.invert(gray)):
        try:
            boxes = _ocr_boxes(variant, scale)
        except Exception:
            return None
        if len(boxes) >= 2:  # обе строки: AVALON и TRAVELERS
            return (
                min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes), max(b[3] for b in boxes),
            )
    return None


def find_watermark(img):
    """Возвращает (region, способ, оценка) или (None, None, оценка)."""
    rgb = img.convert("RGB")
    score = 0.0
    if cv2 is not None:
        score, region = _find_region_template(np.array(rgb))
        if region is not None and score >= MATCH_THRESHOLD:
            return region, "шаблон", score
    region = _find_region_ocr(rgb)
    if region is not None:
        return region, "OCR", score
    return None, None, score


# ---------- удаление ----------

def _inpaint(img, region, thr=12, smax=100):
    """Маска по штрихам внутри region + inpaint OpenCV."""
    arr = np.array(img)
    H, W = arr.shape[:2]

    x1, y1, x2, y2 = region
    pad = 4
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(W, x2 + pad)
    y2 = min(H, y2 + pad)
    if x2 - x1 < 4 or y2 - y1 < 4:
        return img

    mask = _stroke_mask(arr, thr, smax)[y1:y2, x1:x2]
    mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)

    # если маска закрыла почти всё, это не знак, а детали картинки
    coverage = (mask > 0).sum() / mask.size
    if coverage == 0 or coverage > 0.5:
        return img

    # контекст вокруг области, чтобы inpaint видел фон
    cx1, cy1 = max(0, x1 - 10), max(0, y1 - 10)
    cx2, cy2 = min(W, x2 + 10), min(H, y2 + 10)
    full_mask = np.zeros((cy2 - cy1, cx2 - cx1), np.uint8)
    full_mask[y1 - cy1:y2 - cy1, x1 - cx1:x2 - cx1] = mask

    crop = arr[cy1:cy2, cx1:cx2]
    result = cv2.inpaint(crop, full_mask, 3, cv2.INPAINT_TELEA)
    out = arr.copy()
    out[cy1:cy2, cx1:cx2] = result
    return Image.fromarray(out)


def strip_watermark(img):
    alpha = None
    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
        alpha = img.convert("RGBA").getchannel("A")
    rgb = img.convert("RGB")

    region, how, score = find_watermark(rgb)
    if region is None:
        return img  # знак не найден, ничего не трогаем

    if cv2 is None:
        x1, y1, x2, y2 = region
        out = _cover(rgb, x1, y1, x2 - x1, y2 - y1)
    else:
        out = _inpaint(rgb, region)

    if alpha is not None:
        out = out.convert("RGBA")
        out.putalpha(alpha)
    return out


# ---------- работа с файлами ----------

EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def _same(a, b):
    return np.array_equal(np.array(a.convert("RGBA")), np.array(b.convert("RGBA")))


def process_file(src, dst):
    """Возвращает (изменён ли файл, пояснение)."""
    img = Image.open(src)
    img.load()

    region, how, score = find_watermark(img)
    if region is None:
        return False, "знак не найден (оценка %.2f, размер %dx%d)" % (score, img.width, img.height)

    out = strip_watermark(img)
    if dst == src and _same(img, out):
        return False, "маска пустая, файл не тронут"

    ext = os.path.splitext(dst)[1].lower()
    kwargs = {}
    if ext in (".jpg", ".jpeg"):
        if out.mode == "RGBA":  # JPEG не умеет прозрачность
            out = out.convert("RGB")
        kwargs["quality"] = 95

    # сначала пишем во временный файл, потом подменяем:
    # если что-то упадёт на сохранении, оригинал останется целым
    tmp = dst + ".tmp" + ext
    out.save(tmp, **kwargs)
    os.replace(tmp, dst)
    return True, "%s, оценка %.2f" % (how, score)


def process_dir(src_dir, dst_dir):
    if cv2 is None:
        print("ОШИБКА: не установлен OpenCV, поиск знака по шаблону не работает.")
        print("Установи:  pip install opencv-python  (и запусти скрипт тем же Python)")
        return
    print("OpenCV", cv2.__version__)
    os.makedirs(dst_dir, exist_ok=True)
    names = sorted(
        n for n in os.listdir(src_dir)
        if n.lower().endswith(EXTS) and os.path.isfile(os.path.join(src_dir, n))
    )
    if not names:
        print("В папке нет картинок:", src_dir)
        return

    changed = 0
    for n in names:
        try:
            ok, why = process_file(os.path.join(src_dir, n), os.path.join(dst_dir, n))
            if ok:
                changed += 1
            print("%-4s %s - %s" % ("OK" if ok else "SKIP", n, why))
        except Exception as e:
            print("FAIL", n, "-", e)
    print("Готово: изменено %d из %d" % (changed, len(names)))


if __name__ == "__main__":
    # python watermark.py <папка или файл> [куда сохранить]
    # без второго аргумента файлы перезаписываются под тем же именем
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python watermark.py папка [выходная_папка]")
        print("  python watermark.py файл.png [выход.png]")
        sys.exit(1)

    src = sys.argv[1]
    if os.path.isdir(src):
        dst = sys.argv[2] if len(sys.argv) > 2 else src
        process_dir(src, dst)
    else:
        dst = sys.argv[2] if len(sys.argv) > 2 else src
        if cv2 is None:
            print("ОШИБКА: не установлен OpenCV. Установи: pip install opencv-python")
            sys.exit(1)
        ok, why = process_file(src, dst)
        print(("Готово: " if ok else "Пропущено: ") + why)