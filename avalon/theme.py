MAX_SEARCH_LEN = 40
GAP = 8
RADIUS = 14 

BG = "#0e1014"
PANEL = "#1a1d24"
PANEL_MAP = "#12151b"
CARD = "#242831"
CARD_HOVER = "#2e333e"
BORDER = "#303644"

ACCENT = "#3b82f6"
ACCENT_HOVER = "#2f6fdc"
ACCENT_DIM = "#22406e"

TEXT = "#e7e9ee"
TEXT_DIM = "#8a93a3"
TEXT_FAINT = "#566070"

TIER_COLORS = {
    4: "#5aa9ff",
    5: "#ff6b6b",
    6: "#ff9f43",
    7: "#f7d154",
    8: "#e8e8e8",
}


def tier_color(tier):
    return TIER_COLORS.get(tier, TEXT_DIM)