from avalon.libs import *
from avalon.theme import *
ROW_H = 36
class LeftPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        translator: Translator,
        on_search,
        on_enter,
        on_ocr,
        on_paste,
        on_lang,
        on_select,
    ):
        super().__init__(
            master,
            width=290,
            corner_radius=RADIUS,
            fg_color=PANEL,
            border_width=1,
            border_color=BORDER,
        )
        self.tr = translator
        self.on_select = on_select
        self.on_search = on_search
        self.current_maps = []
        self.shown_names = None
        self.selected = None
        self.hover = None
        self.count = 0

        self.grid_propagate(False)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        self.logo = self._load_logo()
        if self.logo:
            ctk.CTkLabel(header, image=self.logo, text="").pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header,
            text=self.tr.t("app_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).pack(side="left")

        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.lang_label = ctk.CTkLabel(
            lang_frame,
            text=self.tr.t("language") + ":",
            text_color=TEXT_DIM,
        )
        self.lang_label.pack(side="left")
        self.lang_btn = ctk.CTkSegmentedButton(
            lang_frame,
            values=["RU", "EN"],
            command=on_lang,
            width=110,
            fg_color=CARD,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=CARD,
            unselected_hover_color=CARD_HOVER,
        )
        self.lang_btn.set("RU" if self.tr.lang == "ru" else "EN")
        self.lang_btn.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text=self.tr.t("search_placeholder"),
            height=40,
            corner_radius=10,
            fg_color=CARD,
            border_color=BORDER,
            border_width=1,
        )
        self.search_entry.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        self.search_entry.bind("<KeyRelease>", self._on_text_change)
        self.search_entry.bind("<Return>", on_enter)
        self.search_entry.bind("<<Paste>>", lambda e: self.after(10, self._on_text_change))
        self.search_entry.bind("<ButtonRelease-2>", lambda e: self.after(10, self._on_text_change))

        ocr_frame = ctk.CTkFrame(self, fg_color="transparent")
        ocr_frame.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 4))

        self.ocr_btn = ctk.CTkButton(
            ocr_frame,
            text="OCR (область)",
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(weight="bold"),
            command=on_ocr,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
        )
        self.ocr_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.paste_btn = ctk.CTkButton(
            ocr_frame,
            text="Из буфера",
            height=36,
            width=100,
            corner_radius=10,
            command=on_paste,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_width=1,
            border_color=BORDER,
        )
        self.paste_btn.pack(side="right")

        self.count_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
            anchor="w",
        )
        self.count_label.grid(row=4, column=0, sticky="ew", padx=18, pady=(8, 0))

        list_wrap = ctk.CTkFrame(self, fg_color="transparent")
        list_wrap.grid(row=5, column=0, sticky="nsew", padx=(8, 4), pady=4)
        list_wrap.grid_rowconfigure(0, weight=1)
        list_wrap.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            list_wrap,
            bg=PANEL,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scroll = ctk.CTkScrollbar(list_wrap, command=self.canvas.yview)
        self.scroll.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-4, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(4, "units"))

        status_box = ctk.CTkFrame(self, fg_color=CARD, corner_radius=10)
        status_box.grid(row=6, column=0, sticky="ew", padx=14, pady=(4, 14))
        self.status = ctk.CTkLabel(
            status_box,
            text=self.tr.t("ocr_status_ready"),
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
            wraplength=230,
            justify="left",
            anchor="w",
        )
        self.status.pack(fill="x", padx=12, pady=10)

    def _load_logo(self):
        path = ASSETS_DIR / "icon.png"
        if not path.exists():
            return None
        try:
            img = Image.open(path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=(34, 34))
        except Exception:
            return None

    def set_status(self, text: str):
        self.status.configure(text=text)

    def search_text(self) -> str:
        return self.search_entry.get().strip().lower()

    def set_search_text(self, text: str):
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, text[:MAX_SEARCH_LEN])

    def _on_text_change(self, event=None):
        if len(self.search_entry.get()) > MAX_SEARCH_LEN:
            self.search_entry.delete(MAX_SEARCH_LEN, "end")
        self.on_search(event)

    def populate(self, maps):
        names = [m["name"] for m in maps]
        if names == self.shown_names:
            return
        self.shown_names = names
        self.current_maps = list(maps)
        self.hover = None
        self.count = len(maps)
        self._update_count()
        self._rebuild()

    def _rebuild(self):
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 220)
        if not self.current_maps:
            self.canvas.create_text(
                width // 2,
                40,
                text=self.tr.t("map_not_found"),
                fill=TEXT_FAINT,
                font=("Arial", 12),
            )
            self.canvas.configure(scrollregion=(0, 0, width, 80))
            return

        for i in range(len(self.current_maps)):
            self._paint_row(i, width)
        self.canvas.configure(scrollregion=(0, 0, width, len(self.current_maps) * ROW_H))

    def _round(self, x1, y1, x2, y2, r, **kwargs):
        r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
        return self.canvas.create_polygon(
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
            smooth=True,
            **kwargs,
        )

    def _paint_row(self, i, width=None):
        self.canvas.delete(f"row{i}")
        m = self.current_maps[i]
        if width is None:
            width = max(self.canvas.winfo_width(), 220)
        y = i * ROW_H
        name = m["name"]
        selected = name == self.selected
        hover = i == self.hover
        bg = ACCENT_DIM if selected else (CARD_HOVER if hover else "")
        tags = (f"row{i}",)
        if bg:
            self._round(
                4, y + 2, width - 6, y + ROW_H - 2,
                8, fill=bg, outline="", tags=tags,
            )
        tier = m.get("tier", "?")
        self._round(
            8, y + 6, 46, y + ROW_H - 6,
            7, fill=tier_color(tier), outline="", tags=tags,
        )
        self.canvas.create_text(
            27, y + ROW_H // 2,
            text=f"T{tier}",
            fill="#101216",
            font=("Arial", 9, "bold"),
            tags=tags,
        )
        self.canvas.create_text(
            54, y + ROW_H // 2,
            text=name,
            anchor="w",
            fill=TEXT,
            font=("Arial", 12),
            tags=tags,
        )

    def _row_at(self, event):
        if not self.current_maps:
            return None
        y = self.canvas.canvasy(event.y)
        idx = int(y // ROW_H)
        if 0 <= idx < len(self.current_maps):
            return idx
        return None

    def _on_click(self, event):
        idx = self._row_at(event)
        if idx is None:
            return
        self.on_select(self.current_maps[idx]["name"])

    def _on_motion(self, event):
        idx = self._row_at(event)
        if idx == self.hover:
            return
        old = self.hover
        self.hover = idx
        self.canvas.configure(cursor="hand2" if idx is not None else "")
        if old is not None:
            self._paint_row(old)
        if idx is not None:
            self._paint_row(idx)

    def _on_leave(self, _event=None):
        old = self.hover
        self.hover = None
        self.canvas.configure(cursor="")
        if old is not None:
            self._paint_row(old)

    def _on_canvas_resize(self, _event=None):
        if self.current_maps or self.shown_names is not None:
            self._rebuild()

    def _on_mousewheel(self, event):
        step = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(step * 3, "units")

    def set_selected(self, name: str):
        old = self.selected
        self.selected = name
        for i, m in enumerate(self.current_maps):
            if m["name"] in (old, name):
                self._paint_row(i)
        for i, m in enumerate(self.current_maps):
            if m["name"] == name:
                total = max(len(self.current_maps) * ROW_H, 1)
                self.canvas.yview_moveto(max(0, (i * ROW_H - ROW_H) / total))
                break

    def _update_count(self):
        word = "Карт" if self.tr.lang == "ru" else "Maps"
        self.count_label.configure(text=f"{word}: {self.count}")

    def apply_language(self):
        self.search_entry.configure(placeholder_text=self.tr.t("search_placeholder"))
        self.lang_label.configure(text=self.tr.t("language") + ":")
        if self.tr.lang == "en":
            self.ocr_btn.configure(text="OCR (region)")
            self.paste_btn.configure(text="Clipboard")
        else:
            self.ocr_btn.configure(text="OCR (область)")
            self.paste_btn.configure(text="Из буфера")
        self._update_count()
        if not self.current_maps:
            self._rebuild()
        if not self.status.cget("text"):
            self.status.configure(text=self.tr.t("ocr_status_ready"))
