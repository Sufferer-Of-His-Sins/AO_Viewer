from avalon.libs import *
from avalon.theme import *

CHEST_COLORS = {"blue": "#4da6ff", "green": "#4dff88", "gold": "#ffd700"}

RESOURCE_COLORS = {
    "wood": "#b07d4f",
    "ore": "#9fb0c3",
    "stone": "#8b93a1",
    "hide": "#d9a066",
    "fiber": "#56d364",
}


class InfoPanel(ctk.CTkFrame):
    def __init__(self, master, translator: Translator, show_chests, show_resources, on_toggle):
        super().__init__(
            master,
            width=300,
            corner_radius=RADIUS,
            fg_color=PANEL,
            border_width=1,
            border_color=BORDER,
        )
        self.tr = translator
        self._tier = None
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        head = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(16, 8))
        head.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(
            head,
            text="—",
            font=ctk.CTkFont(size=20, weight="bold"),
            wraplength=240,
            justify="left",
            anchor="w",
        )
        self.title.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

        self.tier_badge = ctk.CTkLabel(
            head,
            text="",
            width=84,
            height=24,
            corner_radius=7,
            text_color="#101216",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.tier_badge.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))
        self.tier_badge.grid_remove()

        toggle_frame = ctk.CTkFrame(self, fg_color=CARD, corner_radius=12)
        toggle_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        self.chests_cb = ctk.CTkSwitch(
            toggle_frame,
            text=self.tr.t("show_chests"),
            variable=show_chests,
            command=on_toggle,
            progress_color=ACCENT,
        )
        self.chests_cb.pack(anchor="w", padx=14, pady=(12, 6))

        self.resources_cb = ctk.CTkSwitch(
            toggle_frame,
            text=self.tr.t("show_resources"),
            variable=show_resources,
            command=on_toggle,
            progress_color=ACCENT,
        )
        self.resources_cb.pack(anchor="w", padx=14, pady=(6, 12))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=2, column=0, sticky="nsew", padx=14, pady=0)

        self.hotkey_label = ctk.CTkLabel(
            self,
            text=self.tr.t("hotkey_info"),
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM,
            fg_color=CARD,
            corner_radius=10,
            height=34,
        )
        self.hotkey_label.grid(row=3, column=0, sticky="ew", padx=14, pady=(8, 14))

    def set_map_header(self, name: str, tier=None):
        self.title.configure(text=name)
        self._tier = tier
        if tier is None:
            self.tier_badge.grid_remove()
            return
        self.tier_badge.configure(
            text=f"{self.tr.t('tier')}: T{tier}",
            fg_color=tier_color(tier),
        )
        self.tier_badge.grid()

    def apply_language(self):
        self.chests_cb.configure(text=self.tr.t("show_chests"))
        self.resources_cb.configure(text=self.tr.t("show_resources"))
        self.hotkey_label.configure(text=self.tr.t("hotkey_info"))

    def render(self, map_data, show_chests: bool, show_resources: bool):
        for w in self.content.winfo_children():
            w.destroy()
        if not map_data:
            return

        shown = 0
        if show_chests:
            shown += self._render_chests(map_data)
        if show_resources:
            shown += self._render_resources(map_data)
        shown += self._render_dungeons(map_data)

        if shown == 0:
            ctk.CTkLabel(
                self.content,
                text=self.tr.t("no_data"),
                text_color=TEXT_FAINT,
            ).pack(pady=20)

    def _make_card(self, title: str, rows):
        card = ctk.CTkFrame(self.content, fg_color=CARD, corner_radius=12)
        card.pack(fill="x", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 4))

        for i, (color, text, count) in enumerate(rows, start=1):
            ctk.CTkLabel(
                card, text="●", text_color=color, width=16,
                font=ctk.CTkFont(size=14),
            ).grid(row=i, column=0, padx=(14, 4), pady=2)
            ctk.CTkLabel(
                card, text=text, anchor="w", font=ctk.CTkFont(size=13),
            ).grid(row=i, column=1, sticky="w", pady=2)
            ctk.CTkLabel(
                card, text=str(count), anchor="e",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=i, column=2, sticky="e", padx=(4, 14), pady=2)

        ctk.CTkFrame(card, height=8, fg_color="transparent").grid(
            row=len(rows) + 1, column=0, columnspan=3
        )

    def _render_chests(self, map_data) -> int:
        chests = map_data.get("chests", {})
        names = {
            "blue": self.tr.t("blue_chest"),
            "green": self.tr.t("green_chest"),
            "gold": self.tr.t("gold_chest"),
        }
        rows = []
        for key in ("blue", "green", "gold"):
            count = chests.get(key, 0)
            if count > 0:
                rows.append((CHEST_COLORS[key], names[key], count))
        if not rows:
            return 0
        self._make_card(self.tr.t("chests"), rows)
        return 1

    def _render_resources(self, map_data) -> int:
        resources = map_data.get("resources", {})
        rows = []
        for key in ("wood", "ore", "stone", "hide", "fiber"):
            count = resources.get(key, 0)
            if count > 0:
                rows.append((RESOURCE_COLORS[key], self.tr.t(key), count))
        if not rows:
            return 0
        self._make_card(self.tr.t("resources"), rows)
        return 1

    def _render_dungeons(self, map_data) -> int:
        dungeons = map_data.get("dungeons", {})
        rows = []
        if dungeons.get("solo", 0) > 0:
            rows.append(("#c084fc", self.tr.t("dungeon_solo"), dungeons["solo"]))
        if dungeons.get("group", 0) > 0:
            rows.append(("#f472b6", self.tr.t("dungeon_group"), dungeons["group"]))
        if not rows:
            return 0
        title = "Данжи" if self.tr.lang == "ru" else "Dungeons"
        self._make_card(title, rows)
        return 1