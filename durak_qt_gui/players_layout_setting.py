from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class LayoutSetting:
    columns_count: int
    rows_count: int
    setting: List[Tuple[int, int]]


PLAYERS_LAYOUT_SETTINGS = {
    2: LayoutSetting(2, 1, [(0, 0), (1, 0)]),
    3: LayoutSetting(2, 2, [(0, 0), (1, 0), (0, 1)]),
    4: LayoutSetting(2, 2, [(0, 0), (1, 0), (0, 1), (1, 1)]),
    5: LayoutSetting(3, 2, [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)]),
    6: LayoutSetting(3, 2, [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]),
}