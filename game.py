import warnings
from typing import List, Dict, Union
from time import perf_counter

import const
import log
from card_index import Index
from events import GameStart, GameOver, SetTrumpCard, SetTrumpSuit, Attack, SetModes, Defence, Redirect, EndTurn, Hand, \
    TakeFromDeckOrder, AttackCanceled, RedirectCanceled, DefenceCanceled, GameReset, SetGameProperties, \
    ShaperBack, MoveSelfToPos
from game_data import DurakData
from game_properties import GameProperties
from player_data import GlobalPlayerData


class Durak:
    def __init__(self):
        self.properties: GameProperties = None
        self.data: DurakData = None
        self.global_player_data: Dict[int, GlobalPlayerData] = {}
        self.player_modes: Dict[int: int] = None
        self.hand_event_in_queue: Hand = None
        self._event_handlers = []
        self.events_history = []

    def add_event_handler(self, callback):
        self._event_handlers.append(callback)

    def remove_event_handler(self, callback):
        self._event_handlers.remove(callback)

    def game_running(self):
        return self.data is not None

    def handle_event(self, event):
        if self.data is not None:
            for slot in self.data.attack_slots + self.data.defence_slots:
                if slot.cards > 1:
                    log.error("slot with more than one card", event, cards=slot.get_known_existing_cards_indices())

        if isinstance(event, GameStart):
            if self.game_running():
                log.error("game start event while game is running")
            self.data = DurakData(self.properties.players_count, self.properties.lowest_card_rank)
            self.events_history.clear()

        elif isinstance(event, SetGameProperties):
            self.properties = event.properties

        elif isinstance(event, Hand):
            self_player = self.data.players[self.properties.self_position]
            if abs(self_player.probs_container.cards - len(event.cards)) < 0.00001:
                self.handle_hand_event(event)
                self.hand_event_in_queue = None
            else:
                self.hand_event_in_queue = event
        elif isinstance(event, TakeFromDeckOrder):
            self.handle_order_event(event)
            if self.hand_event_in_queue is not None:
                self.handle_hand_event(self.hand_event_in_queue)
                self.hand_event_in_queue = None

        elif isinstance(event, SetTrumpSuit) or isinstance(event, SetTrumpCard):
            self.set_trump(event.trump)

        elif isinstance(event, SetModes):
            self.handle_modes_change(event.modes)

        elif isinstance(event, Attack):
            if self.player_modes is None:
                log.error("handle_event", "Attack", "player_modes is None", attack_player_id=event.player_id,
                          attack_card=event.card)
            self.perform_attack(event.player_id, event.card)
        elif isinstance(event, Defence):
            if self.player_modes is None:
                log.error("handle_event", "Defence", "player_modes is None", card_attack=event.card_attack,
                          card_defense=event.card_defence, player_id=event.player_id)
            self.perform_defence(event.player_id, event.card_attack, event.card_defence)
        elif isinstance(event, Redirect):
            if self.player_modes is None:
                log.error("handle_event", "Redirect", "player_modes is None", attack_player_id=event.redirecting_player,
                          attack_card=event.card)
            self.perform_redirect(event.redirecting_player, event.card)

        elif isinstance(event, AttackCanceled):
            self.cancel_attack(event.card)
        elif isinstance(event, RedirectCanceled):
            self.cancel_redirect(event.card)
        elif isinstance(event, DefenceCanceled):
            self.cancel_defence(event.card_attack, event.card_defence)

        elif isinstance(event, EndTurn):
            self.handle_turn_end(event)

        elif isinstance(event, GameReset):
            self.hand_event_in_queue = None
            self.player_modes = None
            self.data = None
        elif isinstance(event, GameOver):
            self.hand_event_in_queue = None
            self.player_modes = None
            self.data = None

        elif isinstance(event, MoveSelfToPos):
            self.properties.self_position = event.pos

        elif isinstance(event, ShaperBack):
            self.handle_shaper_back(event.cards_to_players)
        else:
            log.error("game", "unknown event type", type=type(event), event=event)

        for callback in self._event_handlers:
            try:
                callback(event)
            except Exception as e:
                log.error("error during post-handling event", e, function=callback, event=event)
                raise e

        self.events_history.append(event)

    def handle_shaper_back(self, cards_to_players):
        for card, player_pos in cards_to_players.items():
            container_to = self.data.players[player_pos].probs_container
            container_from = None
            for slot in self.data.attack_slots + self.data.defence_slots:
                cards = slot.get_known_existing_cards_indices()
                if len(cards) > 1:
                    log.error("game", "handle_shaper_back", "found more than one card in slot", slot_cards=cards, cards_to_players=cards_to_players)
                elif len(cards) == 1 and cards[0] == card:
                    container_from = slot
                if container_from is not None:
                    break
            if container_from is None:
                log.error("game", "handle_shaper_back", "cannot find slot with card", card=card, player=player_pos)
            else:
                self.data.move_card(container_from, container_to, card)


    def handle_modes_change(self, new_modes: dict):
        self.player_modes = new_modes

    def handle_turn_end(self, event: EndTurn):
        for i, mode in self.player_modes.items():
            if mode == 9 or mode == 8 or mode == 7:
                last_victim = i
                break
        else:
            log.error("handle_turn_end", "unable to find last turn victim", modes=self.player_modes)
            return
        if event.taking_player_id is None:
            self.data.move_from_slots_to_container(self.data.get_discard())
        else:
            self.data.move_from_slots_to_container(self.data.players[event.taking_player_id].probs_container)

    def cancel_attack(self, card_attack: Index):
        for slot in range(6):
            if self.data.attack_slots[slot].get(card_attack) > 0.99999:
                self_player = self.data.players[self.properties.self_position]
                self.data.move_card(self.data.attack_slots[slot], self_player.probs_container, card_attack)
                return
        log.error("cancel_attack", "no attack card in slots", card_attack=card_attack)

    def cancel_redirect(self, card_attack: Index):
        for slot in range(6):
            if self.data.attack_slots[slot].get(card_attack) > 0.99999:
                self_player = self.data.players[self.properties.self_position]
                self.data.move_card(self.data.attack_slots[slot], self_player.probs_container, card_attack)
                return
        log.error("cancel_redirect", "no attack card in slots", card_attack=card_attack)

    def cancel_defence(self, card_attack: Index, card_defence: Index):
        for slot in range(6):
            if self.data.attack_slots[slot].get(card_attack) > 0.99999:
                self_player = self.data.players[self.properties.self_position]
                self.data.move_card(self.data.defence_slots[slot], self_player.probs_container, card_defence)
                return
        log.error("cancel_defence", "no attack card in slots", card_attack=card_attack, card_defence=card_defence)

    def perform_attack(self, attack_id, card):
        for slot in range(6):
            if self.data.attack_slots[slot].cards < 0.00001:
                self.data.move_card(self.data.players[attack_id].probs_container, self.data.attack_slots[slot], card)
                return
        log.error("preform_attack", "all slots are busy", attack_id=attack_id, card=card)

    def perform_defence(self, player_defence_id, card_attack, card_defence):
        for slot in range(6):
            if self.data.attack_slots[slot].get(card_attack) > 0.99999:
                self.data.move_card(self.data.players[player_defence_id].probs_container, self.data.defence_slots[slot],
                                    card_defence)
                return
        log.error("perform_defence", "no attack card in slots", player_defence_id=player_defence_id,
                  card_attack=card_attack, card_defence=card_defence)

    def perform_redirect(self, redirecting_player_id, card):
        for slot in range(6):
            if self.data.attack_slots[slot].cards < 0.00001:
                self.data.move_card(self.data.players[redirecting_player_id].probs_container,
                                    self.data.attack_slots[slot], card)
                return
        log.error("perform_redirect", "all slots are busy", attack_id=redirecting_player_id, card=card)

    def set_initial_cards(self, cards: List[Index]):
        for card in cards:
            self.data.set_probability(self.data.players[self.properties.self_position].probs_container, card, 1)

    def set_trump(self, trump: Union[Index, int]):
        if isinstance(trump, int):
            self.data.set_trump_suit(trump)
        elif isinstance(trump, Index):
            self.data.set_trump_card(trump)
        else:
            log.error("Durak.set_trump", "invalid trump", trump)

    def validate_deck(self, cards_count):
        c = self.data.get_deck_with_trump_count()
        if cards_count != c:
            log.error("validate_deck", "error", true_server_count=cards_count, local_count=c)

    def validate_discard(self, discard_cards_count):
        c = self.data.get_discard_count()
        if discard_cards_count != c:
            log.error("validate_discard", "error", true_count=discard_cards_count, in_data_count=c)

    def swap_players(self, player_1_index, player_2_index):
        pass

    def handle_hand_event(self, event):
        self_player = self.data.players[self.properties.self_position]
        for card in event.cards:
            self.data.set_probability(self_player.probs_container, card, 1)

    def handle_order_event(self, event):
        for id_ in event.players_ids:
            self.data.move_card_from_deck_to_player(id_)
