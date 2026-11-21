from avalon.libs import *
from avalon.theme import *


def round_corners(img, radius: int):
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, img.width - 1, img.height - 1), radius=radius, fill=255
    )
    img.putalpha(mask)
    return img


class MapView(ctk.CTkFrame):
    def __init__(self, master, translator: Translator):
        super().__init__(
            master,
            corner_radius=RADIUS,
            fg_color=PANEL_MAP,
            border_width=1,
            border_color=BORDER,
        )
        self.tr = translator
        self._photo_ref = None
        self._pil = None
        self._resize_job = None
        self._last_real = None

        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.placeholder = ctk.CTkLabel(
            self,
            text=self.tr.t("no_map_selected"),
            font=ctk.CTkFont(size=16),
            text_color=TEXT_FAINT,
            justify="center",
        )
        self.placeholder.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.image_label.grid_remove()
        self.bind("<Configure>", self._on_resize)

    def show_placeholder(self, text: str):
        self._pil = None
        self._last_real = None
        self.image_label.grid_remove()
        self.placeholder.configure(text=text)
        self.placeholder.grid()

    def show_map(self, map_data) -> bool:
        img_path = MAPS_DIR / map_data.get("image", "")
        if not img_path.exists():
            self.show_placeholder(f"no image\n{img_path.name}")
            return False
        try:
            img = Image.open(img_path)
            img.draft("RGBA", (1600, 1600))
            img.thumbnail((1600, 1600), Image.Resampling.BILINEAR)
            self._pil = img.convert("RGBA")
            self._last_real = None
        except Exception as e:
            self.show_placeholder(f"Image error:\n{e}")
            return False

        self.placeholder.grid_remove()
        self.image_label.grid()
        self._render()
        return True

    def _on_resize(self, event=None):
        if self._pil is None:
            return
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(150, self._render)

    def _render(self):
        self._resize_job = None
        if self._pil is None:
            return

        try:
            scaling = self._get_widget_scaling()
        except Exception:
            scaling = 1.0

        pad = 28
        avail_w = self.winfo_width() / scaling - pad * 2
        avail_h = self.winfo_height() / scaling - pad * 2
        if avail_w < 50 or avail_h < 50:
            return

        iw, ih = self._pil.size
        scale = min(avail_w / iw, avail_h / ih, 2.0)
        size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
        real = (max(1, int(size[0] * scaling)), max(1, int(size[1] * scaling)))
        if self._last_real is not None:
            if abs(self._last_real[0] - real[0]) < 12 and abs(self._last_real[1] - real[1]) < 12:
                return
        self._last_real = real

        img = self._pil.resize(real, Image.Resampling.BILINEAR)
        img = round_corners(img, int(14 * scaling))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
        self.image_label.configure(image=ctk_img, text="")
        self._photo_ref = ctk_img