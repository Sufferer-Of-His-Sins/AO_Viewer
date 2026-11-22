from avalon.libs import *

def _virtual_screen():
    if sys.platform != "win32":
        return None
    import ctypes

    user32 = ctypes.windll.user32
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass
    x = user32.GetSystemMetrics(76)
    y = user32.GetSystemMetrics(77)
    w = user32.GetSystemMetrics(78)
    h = user32.GetSystemMetrics(79)
    if w > 0 and h > 0:
        return x, y, w, h
    return None


def _screenshot():
    try:
        return ImageGrab.grab(all_screens=True)
    except Exception:
        return ImageGrab.grab()


def grab_region(master):
    master.withdraw()
    master.update_idletasks()
    time.sleep(0.15)

    try:
        shot = _screenshot()
    except Exception:
        master.deiconify()
        master.lift()
        raise

    bounds = _virtual_screen()
    if bounds:
        ox, oy, sw, sh = bounds
    else:
        ox, oy = 0, 0
        sw, sh = shot.width, shot.height

    top = tk.Toplevel(master)
    top.overrideredirect(True)
    top.attributes("-topmost", True)
    top.geometry(f"{sw}x{sh}+{ox}+{oy}")
    top.configure(cursor="crosshair", bg="black")
    top.update_idletasks()

    disp_w = max(top.winfo_width(), 1)
    disp_h = max(top.winfo_height(), 1)
    view = shot.resize((disp_w, disp_h), Image.Resampling.BILINEAR)
    view = ImageEnhance.Brightness(view).enhance(0.55)
    photo = ImageTk.PhotoImage(view)

    canvas = tk.Canvas(top, width=disp_w, height=disp_h, highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=photo, anchor="nw")
    canvas.create_text(
        disp_w // 2,
        28,
        text="Выдели название  Esc - отмена",
        fill="#f2f4f8",
        font=("Arial", 14),
    )
    rect = canvas.create_rectangle(0, 0, 0, 0, outline="#3b82f6", width=2)
    result = {"img": None}
    start = {"x": None, "y": None}

    def press(event):
        start["x"], start["y"] = event.x, event.y
        canvas.coords(rect, event.x, event.y, event.x, event.y)

    def drag(event):
        if start["x"] is None:
            return
        canvas.coords(rect, start["x"], start["y"], event.x, event.y)

    def finish(_event=None):
        if start["x"] is not None and _event is not None:
            x1, y1 = start["x"], start["y"]
            x2, y2 = _event.x, _event.y
            if abs(x2 - x1) > 8 and abs(y2 - y1) > 8:
                sx = shot.width / disp_w
                sy = shot.height / disp_h
                box = (
                    int(min(x1, x2) * sx),
                    int(min(y1, y2) * sy),
                    int(max(x1, x2) * sx),
                    int(max(y1, y2) * sy),
                )
                result["img"] = shot.crop(box)
        top.destroy()

    def cancel(_event=None):
        start["x"] = None
        top.destroy()

    canvas.bind("<ButtonPress-1>", press)
    canvas.bind("<B1-Motion>", drag)
    canvas.bind("<ButtonRelease-1>", finish)
    top.bind("<Escape>", cancel)
    top.focus_force()
    top.wait_window()

    master.deiconify()
    master.lift()
    master.focus_force()
    return result["img"]
