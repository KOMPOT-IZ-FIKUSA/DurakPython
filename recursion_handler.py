import socket
import threading
from typing import List

import const
import events
import game
import game_properties
import log
from card_index import Index
from game_data import DurakData


class Connection:
    def __init__(self, set_result_string_callback):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serialized_string = ""
        self.recursion_client_result = ""
        self.callback = set_result_string_callback
        threading.Thread(target=self.async_handler).start()

    def set_game_state(self, game_: game.Durak):
        if game_.data is None:
            log.error("Connection", "set_game_data", "game data is None")
            return
        assert game_.data.get_deck_with_trump_count() == 0
        assert sum([p.probs_container.cards > 0.0001 for p in game_.data.players]) == 2

        data = game_.data
        players = data.players
        properties = game_.properties
        self_position = properties.self_position

        dict_json_res = {"selfCards": [], "enemyCards": [], "slots": []}
        defender_takes = 7 in game_.player_modes.values()
        dict_json_res["defenderTakes"] = defender_takes
        dict_json_res["selfDefending"] = game_.player_modes[game_.properties.self_position] in (7, 8, 9)
        trump_suit_index = game_.data.trump_suit
        dict_json_res["trump"] = const.suit_names_for_java[const.suits[trump_suit_index]]

        enemy_position = self.get_enemy_index(data, self_position)

        self_player_cards = self.player_cards_to_json_list(players[self_position].get_known_cards())
        enemy_player_cards = self.player_cards_to_json_list(players[enemy_position].get_known_cards())
        slots = self.game_slots_to_json_list(data)

        dict_json_res["selfCards"] = self_player_cards
        dict_json_res["enemyCards"] = enemy_player_cards
        dict_json_res["slots"] = slots
        self.serialized_string = str(dict_json_res)
        print(self.serialized_string)


    def game_slots_to_json_list(self, game_data: DurakData):
        slots = []
        for i in range(6):
            attack_slot = game_data.attack_slots[i]
            defence_slot = game_data.defence_slots[i]
            if attack_slot.cards > 0.0001:
                attack_card = attack_slot.get_known_existing_cards_indices()[0]
                slot = {}
                slot["attack"] = {"absoluteRank": attack_card.absolute,
                                  "suit": const.suit_names_for_java[const.suits[attack_card.suit_i]]}
                if defence_slot.cards > 0.0001:
                    defence_card = defence_slot.get_known_existing_cards_indices()[0]
                    slot["defence"] = {"absoluteRank": defence_card.absolute,
                                       "suit": const.suit_names_for_java[const.suits[defence_card.suit_i]]}
                slots.append(slot)
        return slots

    def get_enemy_index(self, game_data: DurakData, self_position):
        for enemy_index in range(0, len(game_data.players)):
            if enemy_index != self_position and game_data.players[enemy_index].probs_container.cards > 0.0001:
                return enemy_index
        log.error("recursion_handler", "get_enemy_index", "cannot find enemy index", self_position=self_position)

    def player_cards_to_json_list(self, cards: List[Index]):
        res = []
        for card in cards:
            res.append({"absoluteRank": card.absolute, "suit": const.suit_names_for_java[const.suits[card.suit_i]]})
        return res

    def async_handler(self):
        eof = "<eof>".encode("utf-8")
        self.sock.bind(("localhost", 24681))
        self.sock.listen(1)
        buf = bytes()
        conn, addr = None, None
        while True:
            if conn is None:
                conn, addr = self.sock.accept()
            bytes_ = conn.recv(1024)
            buf += bytes_
            while eof in buf:
                index = buf.index(eof)
                packet = buf[:index].decode("utf-8")
                buf = buf[index + 5:]
                if packet == "get":
                    conn.send(self.serialized_string.encode("utf-8") + eof)
                elif packet[:5] == "set":
                    self.recursion_client_result = packet[5:]
                    self.callback(self.recursion_client_result)
                else:
                    log.error("Cannot read packet data", buf, packet)


if __name__ == "__main__":
    c = Connection(print)
    g = game.Durak()
    g.handle_event(
        events.SetGameProperties(game_properties.GameProperties(False, False, False, False, False, 2, 6, 100, 0)))
    g.handle_event(events.GameStart())
    g.handle_event(events.SetTrumpCard(Index(0, 6, 6)))
    g.handle_event(events.TakeFromDeckOrder([0] * 3 + [1] * 33))
    g.handle_event(events.Hand([Index(1, 6, 6), Index(2, 6, 6), Index(3, 6, 6)]))

    c.set_game_state(g)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 24681))
    client.send("get<eof>".encode("utf-8"))
    res = client.recv(1024)
    print(res)
    client.close()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 24681))
    client.send("get<eof>".encode("utf-8"))
    res = client.recv(1024)
    print(res)
    client.close()
    print(res)
