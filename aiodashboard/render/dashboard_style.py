from color_palette import Color # type: ignore[import-untyped]

from dataclasses import dataclass

@dataclass
class DashboardStyle:
    """
    Define a color scheme for the dashboard.
    """
    color_font: Color
    color_main: Color
    color_accent: Color
    color_light: Color
    color_dark: Color
    color_active: Color
    color_bg: Color
    color_body: Color

BLUE_THEME = DashboardStyle(
    Color('004559'), Color('bedaff'),
    Color('229ff2'), Color('f2f7ff'),
    Color('02658c'), Color('fafbfc'),
    Color('eaecef'), Color('fafbfc'),
)

YELLOW_THEME = DashboardStyle(
    Color('562000'), Color('fcd380'),
    Color('e68510'), Color('fffcf2'),
    Color('b65c05'), Color('fcfcfa'),
    Color('ebe9e5'), Color('fcfcfa'),
)

GREEN_THEME = DashboardStyle(
    Color('384f00'), Color('b5f885'),
    Color('77c918'), Color('f6fff2'),
    Color('4f7802'), Color('fcfafc'),
    Color('eae5e9'), Color('fcfafc'),
)
