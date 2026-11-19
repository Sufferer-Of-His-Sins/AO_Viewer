import json
from avalon.paths import LOCALES_DIR


class Translator:
    def __init__(self, lang: str = "ru"):
        self.lang = lang
        self.texts: dict = {}
        self.load()

    def load(self):
        path = LOCALES_DIR / f"{self.lang}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.texts = json.load(f)
        else:
            self.texts = {}

    def set_lang(self, lang: str):
        self.lang = lang
        self.load()

    def t(self, key: str, **kwargs) -> str:
        text = self.texts.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return text