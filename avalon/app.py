from avalon.libs import *

class AvalonMapViewer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Avalon Map Viewer")
        self.geometry("1280x800")
        self.minsize(1000, 650)

        self.tr = Translator("ru")
        self.maps_data = load_maps()
        self.current_map = None
        self.show_chests = ctk.BooleanVar(value=True)
        self.show_resources = ctk.BooleanVar(value=True)
        self.ocr_running = False

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.left = LeftPanel(
            self,
            self.tr,
            on_search=self.on_search,
            on_enter=self.on_search_enter,
            on_ocr=self.trigger_ocr_region,
            on_paste=self.trigger_ocr_clipboard,
            on_lang=self.change_language,
            on_select=self.select_map,
        )
        self.left.grid(row=0, column=0, sticky="nsew")
        self.left.populate(self.maps_data)

        self.map_view = MapView(self, self.tr)
        self.map_view.grid(row=0, column=1, sticky="nsew")

        self.info = InfoPanel(
            self,
            self.tr,
            self.show_chests,
            self.show_resources,
            on_toggle=self.refresh_info,
        )
        self.info.grid(row=0, column=2, sticky="nsew")

        bind_ocr_hotkey(lambda: self.after(0, self.trigger_ocr_region))
        self.after(100, lambda: self.left.search_entry.focus())


    def on_search(self, event=None):
        self.left.populate(filter_maps(self.maps_data, self.left.search_text()))

    def on_search_enter(self, event=None):
        hit = first_search_hit(self.maps_data, self.left.search_text())
        if hit:
            self.select_map(hit["name"])



    def select_map(self, name: str):
        m = find_by_name(self.maps_data, name)
        if not m:
            self.left.set_status(self.tr.t("map_not_found"))
            return

        self.current_map = m
        self.info.set_map_header(m["name"], f"{self.tr.t('tier')}: T{m.get('tier', '?')}")
        self.map_view.show_map(m)
        self.refresh_info()
        self.left.set_status(self.tr.t("ocr_found", name=m["name"]))



    def refresh_info(self):
        self.info.render(
            self.current_map,
            self.show_chests.get(),
            self.show_resources.get(),
        )



    def change_language(self, value):
        self.tr.set_lang("ru" if value == "RU" else "en")
        self.left.apply_language()
        self.info.apply_language()
        if not self.current_map:
            self.map_view.show_placeholder(self.tr.t("no_map_selected"))
            self.left.set_status(self.tr.t("ocr_status_ready"))
        else:
            self.info.set_map_header(
                self.current_map["name"],
                f"{self.tr.t('tier')}: T{self.current_map.get('tier', '?')}",
            )
            self.refresh_info()

    def trigger_ocr_region(self):
        if self.ocr_running:
            return
        self.ocr_running = True
        self.left.set_status(self.tr.t("ocr_status_scanning"))
        threading.Thread(target=self._do_ocr_region, daemon=True).start()



    def trigger_ocr_clipboard(self):
        try:
            text = self.clipboard_get().strip()
        except Exception as e:
            self.left.set_status(f"Clipboard error: {e}")
            return

        if not text:
            self.left.set_status("Буфер обмена пуст")
            return

        found = best_match(self.maps_data, text)
        if found:
            self.select_map(found["name"])
            return

        self.left.set_search_text(text)
        self.on_search()
        self.left.set_status(f"Clipboard: {text}")



    def _do_ocr_region(self):
        try:
            text = read_name_near_cursor()
            if not text:
                self.after(0, lambda: self.left.set_status(self.tr.t("ocr_not_found")))
                return

            found = best_match(self.maps_data, text)
            if found:
                self.after(0, lambda: self.select_map(found["name"]))
            else:
                self.after(0, lambda: self.left.set_status(
                    f"{self.tr.t('ocr_not_found')} ({text})"
                ))
        except Exception as e:
            self.after(0, lambda: self.left.set_status(f"OCR error: {e}"))
        finally:
            self.ocr_running = False