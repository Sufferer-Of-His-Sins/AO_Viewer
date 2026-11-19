from avalon.libs import *

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
        
        super().__init__(master, width=290, corner_radius=0)
        self.tr = translator
        self.on_select = on_select
        self.map_buttons = []

        self.grid_propagate(False)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(14, 4))
        ctk.CTkLabel(lang_frame, text=self.tr.t("language") + ":").pack(side="left")
        self.lang_btn = ctk.CTkSegmentedButton(
            lang_frame,
            values=["RU", "EN"],
            command=on_lang,
            width=110,
        )
        self.lang_btn.set("RU" if self.tr.lang == "ru" else "EN")
        self.lang_btn.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text=self.tr.t("search_placeholder"),
            height=38
        )
        
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        self.search_entry.bind("<KeyRelease>", on_search)
        self.search_entry.bind("<Return>", on_enter)

        ocr_frame = ctk.CTkFrame(self, fg_color="transparent")
        ocr_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))

        self.ocr_btn = ctk.CTkButton(
            ocr_frame,
            text="OCR (область)",
            height=34,
            command=on_ocr,
            fg_color="#1f6aa5",
        )
        self.ocr_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.paste_btn = ctk.CTkButton(
            ocr_frame,
            text="Из буфера",
            height=34,
            width=100,
            command=on_paste,
            fg_color="#3a3a3a",
        )
        self.paste_btn.pack(side="right")

        self.map_listbox = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.map_listbox.grid(row=3, column=0, sticky="nsew", padx=8, pady=4)

        self.status = ctk.CTkLabel(
            self,
            text=self.tr.t("ocr_status_ready"),
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa",
            wraplength=260,
            justify="left",
        )
        self.status.grid(row=4, column=0, sticky="ew", padx=12, pady=(4, 14))

    def set_status(self, text: str):
        self.status.configure(text=text)

    def search_text(self) -> str:
        return self.search_entry.get().strip().lower()

    def set_search_text(self, text: str):
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, text)

    def populate(self, maps):
        for btn in self.map_buttons:
            btn.destroy()
        self.map_buttons.clear()

        for m in maps:
            name = m["name"]
            tier = m.get("tier", "?")
            btn = ctk.CTkButton(
                self.map_listbox,
                text=f"T{tier}  {name}",
                anchor="w",
                height=32,
                fg_color="transparent",
                hover_color=("#3a3a3a", "#2b2b2b"),
                command=lambda n=name: self.on_select(n),
            )
            btn.pack(fill="x", pady=1)
            self.map_buttons.append(btn)

    def apply_language(self):
        self.search_entry.configure(placeholder_text=self.tr.t("search_placeholder"))
        if self.tr.lang == "en":
            self.ocr_btn.configure(text="OCR (region)")
            self.paste_btn.configure(text="Clipboard")
        else:
            self.ocr_btn.configure(text="OCR (область)")
            self.paste_btn.configure(text="Из буфера")
        if not self.status.cget("text"):
            self.status.configure(text=self.tr.t("ocr_status_ready"))
