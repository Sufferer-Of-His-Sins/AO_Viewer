import sys
import threading


def _windows_hotkey(callback) -> bool:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x0002, 0x0004, 0x4000
    VK_Z = 0x5a
    WM_HOTKEY = 0x0312

    result = {}
    ready = threading.Event()

    def loop():
        ok = user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, VK_Z)
        result["ok"] = bool(ok)
        ready.set()
        if not ok:
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                callback()

    threading.Thread(target=loop, daemon=True).start()
    ready.wait(2)
    return result.get("ok", False)


def _linux_hotkey(callback) -> bool:
    from pynput import keyboard

    listener = keyboard.GlobalHotKeys({"<ctrl>+<shift>+z": callback})
    listener.daemon = True
    listener.start()
    return True


def bind_ocr_hotkey(callback) -> bool:
    try:
        if sys.platform == "win32":
            ok = _windows_hotkey(callback)
            if not ok:
                print("[hotkey] Ctrl+Shift+Z is already used by another program")
                return False
        else:
            _linux_hotkey(callback)
        print("[hotkey] Ctrl+Shift+Z registered")
        return True
    except Exception as e:
        print(f"[hotkey] Ctrl+Shift+Z unavailable ({e}). Use the OCR buttons.")
        return False