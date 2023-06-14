import warnings

import const


class Index:
    def __init__(self, suit_i, absolute_rank, lowest_rank):
        self.absolute = absolute_rank
        self.suit_i = suit_i
        self.rank_i = absolute_rank - lowest_rank

    @classmethod
    def from_string(cls, string, lowest_rank):
        res = Index(const.suits.index(string[0]), const.ranks_string_to_value[string[1:]], lowest_rank)
        return res

    @classmethod
    def is_valid_card(cls, string):
        if len(string) < 2 or len(string) > 3:
            return False
        if string[0] not in const.suits:
            return False
        if string[1:] not in const.ranks_string_to_value.keys():
            return False
        return True

    @classmethod
    def is_valid_suit(cls, string):
        return len(string) == 1 and string[0] in const.suits

    def __str__(self):
        ru_name = const.suit_names[const.suits[self.suit_i]]
        return f"Index({ru_name}, {const.ranks_value_to_string[self.absolute]})"

    def __repr__(self):
        ru_name = const.suit_names[const.suits[self.suit_i]]
        return f"Index({ru_name}, {const.ranks_value_to_string[self.absolute]})"

    def to_compact_string(self):
        return const.suits[self.suit_i] + const.ranks_value_to_string[self.absolute]

    def __eq__(self, other):
        return self.absolute == other.absolute and self.suit_i == other.suit_i

    def __hash__(self) -> int:
        return self.absolute * 4 + self.suit_i

