from avalon.libs import *

OCR_CONFIG = (
    r"--oem 3 --psm 7 "
    r"-c tessedit_char_whitelist="
    r"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-"
)


def setup_tesseract():
    exe = "tesseract.exe" if sys.platform == "win32" else "tesseract"
    local = BASE_DIR / "tesseract" / exe
    if local.exists():
        pytesseract.pytesseract.tesseract_cmd = str(local)
        os.environ["TESSDATA_PREFIX"] = str(BASE_DIR / "tesseract" / "tessdata")


setup_tesseract()


def check_tesseract():
    try:
        ver = pytesseract.get_tesseract_version()
        print(f"Tesseract {ver} found")
    except Exception:
        print("-" * 50)
        print("WARNING: Tesseract OCR not found!")
        if sys.platform != "win32":
            print("Ubuntu/Debian:  sudo apt install tesseract-ocr")
        print("-" * 50)


def get_mouse_pos() -> tuple[int, int]:
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            pt = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return pt.x, pt.y
        except Exception:
            pass
    else:
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


def preprocess(img: Image.Image) -> Image.Image:
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img


def recognize(img: Image.Image) -> str:
    text = pytesseract.image_to_string(preprocess(img), config=OCR_CONFIG)
    text = text.strip().replace("\n", "").replace(" ", "")
    return text.replace("|", "I").replace("0", "O")


def read_name_near_cursor() -> str:
    return recognize(capture_around_mouse())