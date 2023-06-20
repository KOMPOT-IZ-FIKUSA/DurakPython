import warnings

import numpy as np

import log
from card_index import Index

class ProbabilityContainer:
    def __init__(self, ranks_count, initial=None):
        if initial is None:
            self.probs = np.zeros((4, ranks_count), dtype=np.float64)
            self.cards = 0
        else:
            self.probs = initial
            self.cards = np.sum(self.probs)
            self.cards : float

    def set_probabilities(self, indices_and_values):
        if self.cards < 0.00001:
            s = 0
            for index, value in indices_and_values:
                self.probs[index.suit_i, index.rank_i] = value
                s += value
            if s > 0.00001:
                log.error("trying to set non-zero probabilities to zero-card container", indices_and_values)
            self.cards = round(np.sum(self.probs))
            return
        delta = 0
        mask = np.where(self.probs < 0.99999, 1, 0)
        for index, value in indices_and_values:
            delta += value - self.probs[index.suit_i, index.rank_i]
            self.probs[index.suit_i, index.rank_i] = value
            mask[index.suit_i, index.rank_i] = 0
        s1 = np.sum(self.probs[mask == 1])
        if s1 > 0.00001:
            k = (self.cards - np.sum(self.probs[mask == 0])) / s1
            self.probs[mask == 1] = self.probs[mask == 1] * k

        self.cards = round(np.sum(self.probs))


    def copy(self):
        return ProbabilityContainer(self.probs.shape[1], self.probs.copy())

    @classmethod
    def random(cls, start_cards, ranks):
        return ProbabilityContainer(ranks, np.zeros((4, ranks), dtype=np.float64) + (start_cards / (ranks * 4)))

    def get(self, index: Index):
        return self.probs[index.suit_i, index.rank_i]

   #def remove_card(self, index: Index):
   #    if self.cards < 0.99999:
   #        log.error(f"Removing card from container with {self.cards} cards.")
   #        self.cards = 0
   #        self.probs *= 0
   #    else:
   #        self.set_probabilities(((index, 1),))
   #        self.cards -= 1
   #        self.probs[index.suit_i, index.rank_i] = 0

    #def add_card(self, index):
    #    if self.cards > 0.00001:
    #        self.set_probabilities(((index, 0),))
    #    self.cards += 1
    #    self.probs[index.suit_i, index.rank_i] = 1

    def clear(self):
        self.cards = 0
        self.probs[:] *= 0

    def __str__(self):
        return str(self.probs)

    def set_cards_count(self, new_count):
        if self.cards < 0.00001 and new_count > 0.00001:
            log.error("trying to set non-zero cards count with to container with zero cards", self.cards, new_count)
        elif self.cards < 0.00001 and new_count < 0.00001:
            pass
        else:
            k = new_count / self.cards
            self.cards *= k
            self.cards = new_count

    def get_known_existing_cards_indices(self):
        ranks_count = self.probs.shape[1]
        lowest_rank = 15 - ranks_count
        indices = np.where(self.probs > 0.99999)
        res = []
        for suit_i, rank_i in zip(*indices):
            res.append(Index(suit_i, rank_i + lowest_rank, lowest_rank))
        return res

    def split_one_card(self):
        if self.cards > 0.99999:
            one_card_split_probs = self.probs / self.cards
            self.cards -= 1
            self.probs -= one_card_split_probs
        else:
            one_card_split_probs = self.probs.copy()
            self.cards = 0
            self.probs[:] = 0
        return ProbabilityContainer(self.probs.shape[1], initial=one_card_split_probs)

    def __add__(self, other):
        return ProbabilityContainer(self.probs.shape[0], self.probs + other.probs)