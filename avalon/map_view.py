from avalon.libs import *


class MapView(ctk.CTkFrame):
    def __init__(self, master, translator: Translator):
        super().__init__(master, corner_radius=0)
        self.tr = translator
        self._photo_ref = None
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.placeholder = ctk.CTkLabel(
            self,
            text=self.tr.t("no_map_selected"),
            font=ctk.CTkFont(size=18),
            text_color="#888888",
        )
        self.placeholder.grid(row=0, column=0, sticky="nsew")

        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.grid(row=0, column=0, sticky="nsew")
        self.image_label.grid_remove()

    def show_placeholder(self, text: str):
        self.image_label.grid_remove()
        self.placeholder.configure(text=text)
        self.placeholder.grid()

    def show_map(self, map_data) -> bool:
        img_path = MAPS_DIR / map_data.get("image", "")
        if not img_path.exists():
            self.show_placeholder(
                f"no image\n{img_path.name}"
            )
            return False
        try:
            pil_img = Image.open(img_path)
            pil_img.thumbnail((720, 680), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=pil_img.size,
            )
            self.image_label.configure(image=ctk_img, text="")
            self._photo_ref = ctk_img
            self.placeholder.grid_remove()
            self.image_label.grid()
            return True
        except Exception as e:
            self.show_placeholder(f"Image error:\n{e}")
            return False