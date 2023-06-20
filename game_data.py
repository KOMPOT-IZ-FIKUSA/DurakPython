import warnings
from typing import List

import numpy as np

import log
from probability_container import ProbabilityContainer as ProbContainer
from card_index import Index
from player import Player


class DurakData:
    def __init__(self, players_count, lowest_rank):
        self._ranks_count = 15 - lowest_rank
        assert players_count * 6 < self._ranks_count * 4
        self.players = [Player(self._ranks_count) for p in range(players_count)]
        self._trump_card = ProbContainer.random(1, self._ranks_count)
        self.trump_suit = None
        self._deck = ProbContainer.random(self._ranks_count * 4 - 1, self._ranks_count)
        self._discard = ProbContainer(self._ranks_count)
        self.attack_slots = [ProbContainer(self._ranks_count) for _ in range(6)]
        self.defence_slots = [ProbContainer(self._ranks_count) for _ in range(6)]

    def get_min_card_rank(self):
        return 15 - self._ranks_count

    def get_discard(self):
        return self._discard

    def set_trump_card(self, index: Index):
        self.set_probability(self._trump_card, index, 1)
        self.trump_suit = index.suit_i

    def set_trump_suit(self, suit_index):
        self.trump_suit = suit_index

    def iterate_over_containers(self):
        for player in self.players:
            yield player.probs_container
        yield self._trump_card
        yield self._deck
        yield self._discard
        for slot in range(6):
            yield self.attack_slots[slot]
            yield self.defence_slots[slot]

    def set_probability(self, container: ProbContainer, index, value):
        p = container.get(index)
        if abs(p - value) < 0.000001:
            return
        container.set_probabilities(((index, value),))
        if abs(p - 1) < 0.0001 and value < 0.0001:
            for cont in self.iterate_over_containers():
                if cont == self._discard:
                    v = 1
                else:
                    v = 0
                cont.set_probabilities(((index, v),))
            return
        k = (1 - value) / (1 - p)
        for cont in self.iterate_over_containers():
            if cont == container:
                continue
            prev_prob = cont.get(index)
            if prev_prob != 0:
                cont.set_probabilities(((index, prev_prob * k),))

    def validate_containers(self):
        sum_ = None
        for p in self.iterate_over_containers():
            if sum_ is None:
                sum_ = p.probs
            else:
                sum_ = sum_ + p.probs
        max_ = np.max(sum_)
        min_ = np.min(sum_)
        return 0.99999 < min_ <= max_ < 1.00001

    def move_card(self, container_from: ProbContainer, container_to: ProbContainer, card: Index):
        if container_from.cards < 0.99999:
            log.error("move_card", "moving card from container with less than one card", card)

        if container_to.cards < 0.00001:
            container_to.cards = 1
            container_to.probs[card.suit_i, card.rank_i] = 1
        else:
            container_to.set_cards_count(container_to.cards + 1)
            container_to.set_probabilities(((card, 1),))

        if container_from.cards < 1.00001:
            container_from.probs *= 0
            container_from.cards = 0
        else:
            container_from.set_cards_count(container_from.cards - 1)
            container_from.set_probabilities(((card, 0),))

        for cont in self.iterate_over_containers():
            if cont == container_to or cont == container_from:
                continue
            cont.set_probabilities(((card, 0),))

    def get_deck_with_trump_count(self):
        return self._deck.cards + self._trump_card.cards

    def get_discard_count(self):
        return self._discard.cards

    def move_from_slots_to_container(self, container):
        for slot in range(6):
            attack = self.attack_slots[slot]
            defence = self.defence_slots[slot]
            if abs(attack.cards - 1) < 0.00001:
                card = attack.get_known_existing_cards_indices()[0]
                self.move_card(attack, container, card)
            if abs(defence.cards - 1) < 0.00001:
                card = defence.get_known_existing_cards_indices()[0]
                self.move_card(defence, container, card)

    def move_card_from_deck_to_player(self, player_id):
        if self._deck.cards > 0.00001:
            splitted_card = self._deck.split_one_card()
            self.players[player_id].probs_container += splitted_card
        elif self._trump_card.cards > 0.00001:
            self.players[player_id].probs_container += self._trump_card
            self._trump_card.cards = 0
            self._trump_card.probs *= 0
        else:
            log.error("DurakData", "move_card_from_deck_to_player", "unable to give card to a player", player_id=player_id)
