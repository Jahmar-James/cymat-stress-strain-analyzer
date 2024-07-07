BLACK = "#000000"
WHITE = "#EEEEEE"

from collections import namedtuple

WINDOW_SIZE = namedtuple("WINDOW_SIZE", ["width", "height"])
CTk_COLOR = namedtuple("CTk_COLOR", ["light", "dark"])

TOP_LEVEL_DEFAULTS = {
    "Size": WINDOW_SIZE(700, 500),
    "foreground": CTk_COLOR(WHITE, BLACK),
}
HEADING_FONT = ("Helvetica", 16, "bold")
SUBHEADING_FONT = ("Helvetica", 14, "bold")
NORMAL_FONT = ("Helvetica", 12)

from pint import UnitRegistry

ureg = UnitRegistry()
