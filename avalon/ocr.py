from avalon.libs import *


def check_tesseract():
    try:
        ver = pytesseract.get_tesseract_version()
        print(f"Tesseract {ver} found")
    except Exception:
        print("WARNING: Tesseract OCR not found.")
        print("Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("Linux:   sudo apt install tesseract-ocr")


def get_mouse_pos() -> tuple[int, int]:
    if sys.platform == "win32":
        import ctypes

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    try:
        out = subprocess.check_output(
            ["xdotool", "getmouselocation", "--shell"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        x = y = 0
        for line in out.splitlines():
            if line.startswith("X="):
                x = int(line.split("=")[1])
            elif line.startswith("Y="):
                y = int(line.split("=")[1])
        return x, y
    except Exception:
        pass

    try:
        screen = ImageGrab.grab()
        return screen.width // 2, 80
    except Exception:
        return 960, 80


def capture_around_mouse(width: int = 450, height: int = 90) -> Image.Image:
    x, y = get_mouse_pos()
    left = max(0, int(x - width // 2))
    top = max(0, int(y - height // 2))
    return ImageGrab.grab(bbox=(left, top, left + width, top + height))


_OCR_FIX = str.maketrans({"0": "O", "1": "I", "|": "I", "5": "S", "8": "B"})
_WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"


def _prepare(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    if img.width < 500:
        factor = 3 if img.width < 220 else 2
        img = img.resize((img.width * factor, img.height * factor), Image.Resampling.LANCZOS)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    return ImageEnhance.Sharpness(img).enhance(2.0)


def _clean_piece(text: str) -> str:
    text = text.translate(_OCR_FIX)
    return "".join(ch for ch in text if ch.isalpha() or ch == "-").strip("-")


def _read_variants(img: Image.Image) -> list[str]:
    base = _prepare(img)
    pictures = (base, ImageOps.invert(base))
    found = []
    for picture in pictures:
        for psm in (7, 13, 6):
            config = f"--oem 3 --psm {psm} -c tessedit_char_whitelist={_WHITELIST}"
            try:
                raw = pytesseract.image_to_string(picture, config=config)
            except Exception:
                continue
            parts = []
            for line in raw.replace("\r", "\n").split("\n"):
                piece = _clean_piece(line)
                if len(piece) >= 4:
                    parts.append(piece)
            if not parts:
                continue
            joined = _clean_piece("".join(parts))
            for item in parts + [joined]:
                if len(item) >= 6 and item not in found:
                    found.append(item)
    return found


def recognize(img: Image.Image) -> str:
    variants = _read_variants(img)
    return variants[0] if variants else ""

def recognize_candidates(img: Image.Image) -> list[str]:
    return _read_variants(img)


def read_name_near_cursor() -> str:
    return recognize(capture_around_mouse())