import os.path
from functools import lru_cache

from PyQt5.Qt import *

import const


@lru_cache(None)
def load_cards() -> dict:
    res = {}
    for index, suit in enumerate(const.suits):
        suit_name = const.suit_names_for_java[suit]
        res[index] = {}
        for rank_value, rank_name in const.ranks_value_to_string.items():
            path = os.path.join("data\\cards_img", f"{suit_name.lower()}_{rank_name}.png")
            img = QPixmap(path, "rgba")

            res[index][rank_value] = img
    res["shirt"] = QPixmap("data\\cards_img\\shirt.png")
    return res
