import enum
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Union

import numpy as np

@dataclass(frozen=True)
class Card:
    suit_index: int  # 0 if trump
    absolute_rank: int

    def beats(self, other):
        if self.suit_index == 0:
            if other.suit_index == 0:
                return self.absolute_rank > other.absolute_rank
            else:
                return True
        else:
            if other.suit_index == 0:
                return False
            elif self.suit_index == other.suit_index:
                return self.absolute_rank > other.absolute_rank
            else:
                return False

    def get_index(self, ranks_count):
        min_rank = 15 - ranks_count
        return self.suit_index * ranks_count + self.absolute_rank - min_rank

    def __hash__(self) -> int:
        return self.suit_index * 12345 + self.absolute_rank * 123

    def __eq__(self, other):
        return self.suit_index == other.suit_index and self.absolute_rank == other.absolute_rank

    def __str__(self):
        return f"{self.suit_index}_{self.absolute_rank}"

    def __repr__(self):
        return self.__str__()



@dataclass
class DefenceTurn:
    card_attack: Card
    card_defence: Card
    defence_player: int

    def __hash__(self) -> int:
        return self.card_attack.__hash__() + self.card_defence.__hash__()


@dataclass
class AttackTurn:
    card: Card
    attack_player: int
    defence_player: int

    def __hash__(self) -> int:
        return self.card.__hash__()


@dataclass
class PassTurn:
    player: int

    def __hash__(self):
        return 1


@dataclass
class TakeTurn:
    player: int

    def __hash__(self):
        return 2


@lru_cache(None)
def get_turn_absolute_index(turn, ranks_count):
    min_rank = 15 - ranks_count
    pass_turns = 1
    take_turns = 1
    attack_turns = ranks_count * 4
    defence_turns = 144 + 243
    if isinstance(turn, PassTurn):
        return 0
    elif isinstance(turn, TakeTurn):
        return 1
    elif isinstance(turn, AttackTurn):
        return 2 + turn.card.suit_index * ranks_count + turn.card.absolute_rank - min_rank
    elif isinstance(turn, DefenceTurn):
        i = 0
        b = False
        for rank_i_attack in range(min_rank, 15):
            for suit_i_attack in range(4):
                for rank_i_defence in range(min_rank, 15):
                    for suit_i_defence in range(4):
                        a = Card(suit_i_attack, rank_i_attack)
                        d = Card(suit_i_defence, rank_i_defence)
                        if a == turn.card_attack and d == turn.card_defence:
                            b = True
                            break
                        if d.beats(a):
                            i += 1
                    if b:
                        break
                if b:
                    break
            if b:
                break
        return 2 + attack_turns + i
    else:
        raise ValueError

def get_all_possible_turns_count(ranks_count):
    min_rank = 15 - ranks_count
    pass_turns = 1
    take_turns = 1
    attack_turns = ranks_count * 4
    defence_turns = 144 + 243
    return pass_turns + take_turns + attack_turns + defence_turns


class PlayerState(enum.Enum):
    ATTACK = 0
    BLOCK = 1
    PASS = 2
    DEFENCE = 3
    TAKE = 4
    WON = 5

@dataclass
class Slot:
    attack: Card
    defence: Card

class CycledList(list):
    def __getitem__(self, index):
        index = index % len(self)
        return super().__getitem__(index)

    def pop(self, index):
        index = index % len(self)
        return super().pop(index)

@dataclass
class Player:
    cards: CycledList
    state: PlayerState

def index(lst, condition):
    for i, elem in enumerate(lst):
        if condition(elem):
            return i

class PlayerList:
    def __init__(self, players: List[Player]):
        self._players = CycledList(players)

    def get_by_id(self, id_) -> Player:
        return self._players[id_]

    def get_active_players_count(self) -> int:
        return sum([p.state != PlayerState.WON for p in self._players])

    def get_next_active_player(self, player: Union[int, Player]) -> Player:
        assert self.get_active_players_count() >= 2
        if isinstance(player, Player):
            player = self._players.index(player)
        for delta in range(1, len(self._players)):
            i = (player + delta) % len(self._players)
            if self._players[i].state != PlayerState.WON:
                return self._players[i]
        raise ValueError

    def set_main_attacker_and_block_others(self, main_attacker_index):
        for player in self._players:
            if player.state != PlayerState.WON:
                player.state = PlayerState.BLOCK
        self._players[main_attacker_index].state = PlayerState.ATTACK
        self.get_next_active_player(main_attacker_index).state = PlayerState.DEFENCE

    def set_pass_and_unblock(self, pass_player_index):
        for i, p in enumerate(self._players):
            if i == pass_player_index:
                p.state = PlayerState.PASS
            elif p.state == PlayerState.BLOCK:
                p.state = PlayerState.ATTACK

    def all_attackers_passed(self) -> bool:
        for p in self._players:
            if p.state == PlayerState.ATTACK:
                return False
        return True

    def defender_takes(self) -> bool:
        for p in self._players:
            if p.state == PlayerState.TAKE:
                return True
            elif p.state == PlayerState.DEFENCE:
                return False
        raise ValueError

    def get_taking_player(self) -> Player:
        for p in self._players:
            if p.state == PlayerState.TAKE:
                return p
        raise ValueError

    def get_deck_distribution_order(self) -> List[int]:
        assert all([p.state in (PlayerState.DEFENCE, PlayerState.TAKE, PlayerState.PASS) for p in self._players])
        assert sum([int(p.state == PlayerState.TAKE or p.state == PlayerState.DEFENCE) for p in self._players]) == 1
        all_ids = list(range(len(self._players)))
        defender_id = index(self._players, lambda p: p.state == PlayerState.DEFENCE or p.state == PlayerState.TAKE)
        if defender_id == 0:
            main_attacker_id = len(all_ids) - 1
            other_attackers = all_ids[1:-1]
        else:
            main_attacker_id = defender_id - 1
            other_attackers = all_ids[defender_id + 1:] + all_ids[:defender_id - 1]
        res = [main_attacker_id] + other_attackers + [defender_id]
        return res

    def handle_turn_end_states(self):
        old_defender_index = index(self._players, lambda p: p.state == PlayerState.TAKE or p.state == PlayerState.DEFENCE)
        players_before_old_def = [self._players[i] for i in range(old_defender_index + 1, old_defender_index + len(self._players) + 1)] # [player, player, player ... old_def]
        old_defender = players_before_old_def[-1]
        if old_defender.state == PlayerState.TAKE:
            old_defender.state = PlayerState.BLOCK
            attack_player_selected = False
            defence_player_selected = False
            old_defender_state_changed = False
        else:
            if len(old_defender.cards) == 0:
                old_defender.state = PlayerState.WON
                attack_player_selected = False
                defence_player_selected = False
                old_defender_state_changed = True
            else:
                old_defender.state = PlayerState.ATTACK
                attack_player_selected = True
                defence_player_selected = False
                old_defender_state_changed = True

        for p in players_before_old_def:
            if p.state == PlayerState.WON:
                assert len(p.cards) == 0
            if p == old_defender and old_defender_state_changed:
                continue
            if len(p.cards) == 0:
                p.state = PlayerState.WON
            else:
                if attack_player_selected:
                    if defence_player_selected:
                        p.state = PlayerState.BLOCK
                    else:
                        p.state = PlayerState.DEFENCE
                        defence_player_selected = True
                else:
                    p.state = PlayerState.ATTACK
                    attack_player_selected = True

    def get_defending_or_taking(self) -> Player:
        for p in self._players:
            if p.state == PlayerState.TAKE or p.state == PlayerState.DEFENCE:
                return p
        raise ValueError

    def __str__(self):
        return str(self._players)

    def index(self, player):
        assert player in self._players
        return self._players.index(player)

    def iterfrom(self, player_index):
        for i in range(player_index, player_index + len(self._players)):
            yield self._players[i]

#lst = PlayerList([Player([1, 2], PlayerState.PASS), Player([1, 2], PlayerState.DEFENCE), Player([1, 2], PlayerState.PASS), Player([1, 2], PlayerState.PASS)])
#lst.handle_game_end_states()
#print(lst)
#quit()

class Game:
    def __init__(self, min_rank, ranks_count, players_count):
        self.deck = []
        for rank in range(min_rank, min_rank + ranks_count):
            for suit_i in range(4):
                self.deck.append(Card(suit_i, rank))
        random.shuffle(self.deck)
        players = []
        r = random.randint(0, players_count - 2)
        states = r * [PlayerState.BLOCK] + [PlayerState.ATTACK, PlayerState.DEFENCE] + (players_count - 2 - r) * [PlayerState.BLOCK]
        assert len(states) == players_count
        for state in states:
            players.append(Player(CycledList([self.pop_deck() for _ in range(6)]), state))

        self.players = PlayerList(players)
        self.slots = []
        self.slots: List[Slot]
        self.ranks_count = ranks_count
        self._game_ended = False

    def pop_deck(self):
        assert len(self.deck) > 0
        return self.deck.pop(0)

    def apply_turn(self, turn):
        assert not self._game_ended
        if isinstance(turn, AttackTurn):
            self.handle_attack(turn)
        elif isinstance(turn, DefenceTurn):
            self.handle_defence(turn)
        elif isinstance(turn, TakeTurn):
            self.handle_take(turn)
        elif isinstance(turn, PassTurn):
            self.handle_pass(turn)
        else:
            raise ValueError
        self.handle_turn_end()

    def game_ended(self):
        return self._game_ended

    def can_redirect(self, current_player: Player, next_player: Player, card):
        assert current_player.state == PlayerState.DEFENCE
        if len(self.slots) == 0:
            return False
        if card.absolute_rank != self.slots[0].attack.absolute_rank:
            return False
        if self.get_uncovered_slots_count() != len(self.slots):
            return False
        next_player_cards = next_player.cards
        return len(next_player_cards) >= len(self.slots) + 1

    def handle_attack(self, turn: AttackTurn):
        attack_player = self.players.get_by_id(turn.attack_player)
        assert turn.card in attack_player.cards
        if attack_player.state == PlayerState.DEFENCE:
            # redirect
            new_defending_player = self.players.get_by_id(turn.defence_player)
            assert self.can_redirect(attack_player, new_defending_player, turn.card)
            attack_player.cards.remove(turn.card)
            self.slots.append(Slot(turn.card, None))
            self.players.set_main_attacker_and_block_others(turn.attack_player)

        elif attack_player.state == PlayerState.ATTACK or attack_player.state == PlayerState.PASS:
            # attack lol
            assert self.can_be_attacked_with_card(attack_player, self.players.get_defending_or_taking(), turn.card)
            attack_player.cards.remove(turn.card)
            self.slots.append(Slot(turn.card, None))
        else:
            raise ValueError

    def handle_defence(self, turn: DefenceTurn):
        defence_player = self.players.get_by_id(turn.defence_player)
        assert defence_player.state == PlayerState.DEFENCE
        assert turn.card_defence in defence_player.cards
        for slot in self.slots:
            if slot.attack == turn.card_attack:
                assert slot.defence is None
                slot.defence = turn.card_defence
                defence_player.cards.remove(turn.card_defence)
                return
        raise ValueError(f"No slot with attack card {turn.card_attack}")

    def handle_take(self, turn):
        p = self.players.get_by_id(turn.player)
        assert p.state == PlayerState.DEFENCE
        assert self.get_uncovered_slots_count() > 0
        p.state = PlayerState.TAKE

    def handle_pass(self, turn):
        p = self.players.get_by_id(turn.player)
        if p.state == PlayerState.ATTACK:
            self.players.set_pass_and_unblock(turn.player)
        elif p.state == PlayerState.PASS:
            pass
        else:
            raise ValueError

    def get_uncovered_slots_count(self):
        return sum([1 for slot in self.slots if slot.defence is None])

    def handle_turn_end(self):
        if self.players.all_attackers_passed():
            if self.players.defender_takes():
                assert len(self.slots) > 0
                taking_player = self.players.get_taking_player()
                self.perform_take(taking_player)
                assert len(self.slots) == 0
            elif self.get_uncovered_slots_count() == 0:
                self.slots.clear()

            if len(self.deck) > 0:
                order = self.players.get_deck_distribution_order()
                self.perform_deck_distribution(order)
            self.players.handle_turn_end_states()

        if self.players.get_active_players_count() <= 1:
            self._game_ended = True

    def perform_deck_distribution(self, order):
        for player_id in order:
            player = self.players.get_by_id(player_id)
            while len(player.cards) < 6 and len(self.deck) > 0:
                player.cards.append(self.pop_deck())

    def perform_take(self, player: Player):
        assert len(self.slots) > 0
        cards = player.cards
        for s in self.slots:
            cards.append(s.attack)
            if s.defence is not None:
                cards.append(s.defence)
        self.slots.clear()

    def can_be_attacked_with_card(self, attacking_player: Player, defending_player: Player, card):
        assert attacking_player.state == PlayerState.ATTACK or attacking_player.state == PlayerState.PASS
        assert defending_player.state == PlayerState.DEFENCE or defending_player.state == PlayerState.TAKE
        if len(self.slots) == 0:
            return True
        if len(self.slots) == 6:
            return False
        cards_left = len(defending_player.cards) - self.get_uncovered_slots_count()
        if cards_left == 0:
            return False
        for slot in self.slots:
            if slot.attack.absolute_rank == card.absolute_rank or (slot.defence is not None and slot.defence.absolute_rank == card.absolute_rank):
                return True
        return False

    def get_available_turns(self, player_index):
        assert not self._game_ended
        p = self.players.get_by_id(player_index)
        p: Player
        state = p.state
        cards = p.cards
        assert state != PlayerState.WON
        res_lst = []
        if state == PlayerState.PASS or state == PlayerState.ATTACK:
            if (len(self.slots) > 0 and self.get_uncovered_slots_count() == 0) or self.players.get_defending_or_taking().state == PlayerState.TAKE:
                res_lst.append(PassTurn(player_index))
            for card in cards:
                if self.can_be_attacked_with_card(p, self.players.get_defending_or_taking(), card):
                    res_lst.append(AttackTurn(card, player_index, player_index + 1))
        elif state == PlayerState.BLOCK or state == PlayerState.TAKE:
            pass
        elif state == PlayerState.DEFENCE:
            if len(self.slots) != 0:
                if self.get_uncovered_slots_count() > 0:
                    res_lst.append(TakeTurn(player_index))
                next_player_has_cards_redirect_condition = len(self.players.get_next_active_player(p).cards) >= len(self.slots) + 1
                for card in cards:
                    can_redirect = next_player_has_cards_redirect_condition
                    redirect_slot_rank = card.absolute_rank
                    for slot in self.slots:
                        if slot.defence is None:
                            if card.beats(slot.attack):
                                res_lst.append(DefenceTurn(slot.attack, card, player_index))
                            if slot.attack.absolute_rank != redirect_slot_rank:
                                can_redirect = False
                        else:
                            can_redirect = False
                    if can_redirect:
                        next_defending_player = self.players.get_next_active_player(p)
                        next_defending_player = self.players.index(next_defending_player)
                        res_lst.append(AttackTurn(card, player_index, next_defending_player))
        else:
            raise ValueError
        return [(get_turn_absolute_index(turn, self.ranks_count), turn) for turn in res_lst]
