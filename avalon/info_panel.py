from avalon.libs import *


class InfoPanel(ctk.CTkFrame):
    def __init__(self, master, translator: Translator, show_chests, show_resources, on_toggle):
        super().__init__(master, width=300, corner_radius=0)
        self.tr = translator
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(size=20, weight="bold"),
            wraplength=270,
        )
        self.title.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 4))

        self.tier = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#aaaaaa",
        )
        self.tier.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=8)

        self.chests_cb = ctk.CTkCheckBox(
            toggle_frame,
            text=self.tr.t("show_chests"),
            variable=show_chests,
            command=on_toggle,
        )
        self.chests_cb.pack(anchor="w", pady=4)

        self.resources_cb = ctk.CTkCheckBox(
            toggle_frame,
            text=self.tr.t("show_resources"),
            variable=show_resources,
            command=on_toggle,
        )
        self.resources_cb.pack(anchor="w", pady=4)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=3, column=0, sticky="nsew", padx=16, pady=12)
        self.grid_rowconfigure(3, weight=1)

        self.hotkey_label = ctk.CTkLabel(
            self,
            text=self.tr.t("hotkey_info"),
            font=ctk.CTkFont(size=12),
            text_color="#666666",
        )
        self.hotkey_label.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))

    def set_map_header(self, name: str, tier_text: str):
        self.title.configure(text=name)
        self.tier.configure(text=tier_text)

    def apply_language(self):
        self.chests_cb.configure(text=self.tr.t("show_chests"))
        self.resources_cb.configure(text=self.tr.t("show_resources"))
        self.hotkey_label.configure(text=self.tr.t("hotkey_info"))

    def render(self, map_data, show_chests: bool, show_resources: bool):
        for w in self.content.winfo_children():
            w.destroy()
        if not map_data:
            return

        row = 0
        if show_chests:
            row = self._render_chests(map_data, row)
        if show_resources:
            row = self._render_resources(map_data, row)
        self._render_dungeons(map_data, row)

    def _render_chests(self, map_data, row: int) -> int:
        chests = map_data.get("chests", {})
        if not any(v > 0 for v in chests.values()):
            return row

        ctk.CTkLabel(
            self.content,
            text=self.tr.t("chests"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(8, 4))
        row += 1

        color_map = {
            "blue": ("#4da6ff", self.tr.t("blue_chest")),
            "green": ("#4dff88", self.tr.t("green_chest")),
            "gold": ("#ffd700", self.tr.t("gold_chest")),
        }
        for key in ("blue", "green", "gold"):
            count = chests.get(key, 0)
            if count <= 0:
                continue
            color, label = color_map[key]
            frame = ctk.CTkFrame(self.content, fg_color="transparent")
            frame.grid(row=row, column=0, sticky="w", pady=2)
            ctk.CTkLabel(
                frame, text="●", text_color=color, font=ctk.CTkFont(size=16),
            ).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                frame, text=f"{label}: {count}", font=ctk.CTkFont(size=13),
            ).pack(side="left")
            row += 1
        return row

    def _render_resources(self, map_data, row: int) -> int:
        resources = map_data.get("resources", {})
        if not any(v > 0 for v in resources.values()):
            return row

        ctk.CTkLabel(
            self.content,
            text=self.tr.t("resources"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(12, 4))
        row += 1

        res_names = {
            "wood": self.tr.t("wood"),
            "ore": self.tr.t("ore"),
            "stone": self.tr.t("stone"),
            "hide": self.tr.t("hide"),
            "fiber": self.tr.t("fiber"),
        }
        for key, label in res_names.items():
            count = resources.get(key, 0)
            if count <= 0:
                continue
            ctk.CTkLabel(
                self.content,
                text=f"  {label}: {count}",
                font=ctk.CTkFont(size=13),
            ).grid(row=row, column=0, sticky="w", pady=1)
            row += 1
        return row

    def _render_dungeons(self, map_data, row: int):
        dungeons = map_data.get("dungeons", {})
        if dungeons.get("solo", 0) <= 0 and dungeons.get("group", 0) <= 0:
            return
        ctk.CTkLabel(
            self.content,
            text="Dungeons",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(12, 4))
        row += 1
        if dungeons.get("solo", 0) > 0:
            ctk.CTkLabel(
                self.content,
                text=f"  {self.tr.t('dungeon_solo')}: {dungeons['solo']}",
                font=ctk.CTkFont(size=13),
            ).grid(row=row, column=0, sticky="w")
            row += 1
        if dungeons.get("group", 0) > 0:
            ctk.CTkLabel(
                self.content,
                text=f"  {self.tr.t('dungeon_group')}: {dungeons['group']}",
                font=ctk.CTkFont(size=13),
            ).grid(row=row, column=0, sticky="w")