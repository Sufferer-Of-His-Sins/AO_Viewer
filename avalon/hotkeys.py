import sys


def bind_ocr_hotkey(callback) -> bool:
    try:
        if sys.platform == "win32":
            import keyboard
            keyboard.add_hotkey("ctrl+shift+a", callback, suppress=False)
        else:
            from pynput import keyboard
            listener = keyboard.GlobalHotKeys({"<ctrl>+<shift>+a": callback})
            listener.daemon = True
            listener.start()
        print("[hotkey] Ctrl+Shift+A registered")
        return True
    except Exception as e:
        print(f"[hotkey] Ctrl+Shift+A unavailable ({e}). Use the OCR buttons.")
        return False