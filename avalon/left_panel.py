from avalon.libs import *
from avalon.theme import *

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
        self.cache = {}
        self.buttons = {}
        self.rows = []
        self.shown_names = None
        self.selected = None
        self.count = 0
        self.empty_label = None

        self.grid_propagate(False)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        self.logo = self._load_logo()
        if self.logo: ctk.CTkLabel(header, image=self.logo, text="").pack(side="left", padx=(0, 10))
        
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

        self.map_listbox = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=CARD_HOVER,
            scrollbar_button_hover_color=BORDER,
        )
        self.map_listbox.grid(row=5, column=0, sticky="nsew", padx=(8, 4), pady=4)

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

        for row in self.rows:
            row.pack_forget()
        self.rows = []
        if self.empty_label:
            self.empty_label.pack_forget()

        self.count = len(maps)
        self._update_count()

        if not maps:
            if not self.empty_label:
                self.empty_label = ctk.CTkLabel(
                    self.map_listbox,
                    text=self.tr.t("map_not_found"),
                    text_color=TEXT_FAINT,
                )
            self.empty_label.pack(pady=24)
            return

        for m in maps:
            row = self._get_row(m)
            row.pack(fill="x", pady=1)
            self.rows.append(row)

    def _get_row(self, m):
        name = m["name"]
        if name in self.cache:
            return self.cache[name]

        tier = m.get("tier", "?")
        row = ctk.CTkFrame(self.map_listbox, fg_color="transparent")

        badge = ctk.CTkLabel(
            row,
            text=f"T{tier}",
            width=34,
            height=24,
            corner_radius=7,
            fg_color=tier_color(tier),
            text_color="#101216",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        badge.pack(side="left", padx=(4, 6))
        badge.bind("<Button-1>", lambda e, n=name: self.on_select(n))

        btn = ctk.CTkButton(
            row,
            text=name,
            anchor="w",
            height=34,
            corner_radius=8,
            fg_color=ACCENT_DIM if name == self.selected else "transparent",
            hover_color=CARD_HOVER,
            text_color=TEXT,
            command=lambda n=name: self.on_select(n),
        )
        btn.pack(side="left", fill="x", expand=True)

        self.cache[name] = row
        self.buttons[name] = btn
        return row

    def set_selected(self, name: str):
        self.selected = name
        for n, btn in self.buttons.items():
            btn.configure(fg_color=ACCENT_DIM if n == name else "transparent")

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
        if self.empty_label:
            self.empty_label.configure(text=self.tr.t("map_not_found"))
        if not self.status.cget("text"):
            self.status.configure(text=self.tr.t("ocr_status_ready"))