import json
import time
import traceback

from scapy.all import AsyncSniffer

from scapy.layers.inet import TCP

import card_index
import const
import events
import log
from const import SERVER_IP
from game import Durak
from game_properties import GameProperties
from log import error
from player_data import GlobalPlayerData


def load_json(string):
    try:
        return json.loads(string)
    except json.JSONDecodeError:
        error("durak_sniffer.py", "load_json", string)
        return {}


class NamedDict(dict):
    def __init__(self, packet_string: str):
        if "{" not in packet_string and "}" not in packet_string:
            name = packet_string
            data = {}
        elif len(packet_string) < 2 or packet_string[-1] != "}" or "{" not in packet_string:
            error("NamedDict:__init__", "Unable to read dict", packet_string)
            name = ""
            data = {}
        else:
            i = packet_string.index("{")
            name = packet_string[:i]
            data = load_json(packet_string[i:])

        super().__init__(data)
        self.name = name

    def __str__(self):
        return self.name + super().__repr__()

    def __repr__(self):
        return self.name + "{...}"

    def copy(self):
        new_ = NamedDict("{}")
        new_.name = self.name
        for k, v in self.items():
            new_[k] = v
        return new_


class Buffer:
    a = '{'.encode("utf-8")
    b = '}'.encode("utf-8")
    c = '\n'.encode("utf-8")
    bc = b + c

    def __init__(self):
        self.bytes_ = None

    def write_bytes(self, bytes_):
        assert isinstance(bytes_, bytes)
        if self.bytes_ is None:
            self.bytes_ = bytes_
        else:
            self.bytes_ += bytes_

    def read_packet(self):
        if self.c in self.bytes_ and self.a in self.bytes_:
            if self.bytes_.index(self.c) < self.bytes_.index(self.a):  # strings like "abc\ndef{\"value\": 1}\n"
                i = self.bytes_.index(self.c)
                if i == 0:
                    self.bytes_ = self.bytes_[1:]
                    return self.read_packet()
                else:
                    s = self.bytes_[:i].decode("utf-8", errors="replace")
                    self.bytes_ = self.bytes_[i + 1:]
                    return s
        if self.bc in self.bytes_:
            i = self.bytes_.index(self.bc)
            s = self.bytes_[:i + 1].decode("utf-8", errors="replace")
            self.bytes_ = self.bytes_[i + 1:]
            while s[0] == "\n":
                s = s[1:]
            return s
        return None


class DurakSniffer:
    def __init__(self):
        self.capture = AsyncSniffer(iface="Ethernet", count=0, prn=self.callback,
                                    filter="tcp and src host 65.21.92.166 or dst host 65.21.92.166")
        self.game = Durak()
        self.recv_buf = Buffer()
        self.send_buf = Buffer()

    def start(self):
        self.capture.start()

    def some_test(self):
        print('-' * 100)
        if self.game.data:
            for i in self.game.global_player_data:
                user_data = self.game.global_player_data[i]
                if user_data:
                    name = user_data if not user_data else user_data.name
                else:
                    name = "None"
                name += " " * (40 - len(name))
                cards = ""
                for card in self.game.data.players[i].probs_container.get_known_existing_cards_indices():
                    cards += card.to_compact_string() + " "
                print(f"{name} | {cards}")

    def handle_client_packet(self, bytes_: bytes):
        #try:
        #    self.some_test()
        #except Exception as e:
        #    log.error(e)

        self.recv_buf.write_bytes(bytes_)
        packet_str = self.recv_buf.read_packet()
        dicts = []
        while packet_str is not None:
            d = NamedDict(packet_str)
            if d.name:
                dicts.append(d)
            packet_str = self.recv_buf.read_packet()

        name0 = None
        while len(dicts) > 0:
            d = dicts[0]

            name0 = name0 or d.name
            handled = True
            if d.name == "game":
                if "alert" not in d:
                    properties = GameProperties(
                        lowest_card_rank=15 - d["deck"] // 4,
                        draw=not d["sw"],
                        shapers=not d["nb"],
                        redirect=not d["dr"],
                        secondary_attack_sides_only=d["dr"],
                        fast=d["fast"],
                        bet=d["bet"],
                        players_count=d["players"],
                        self_position=d["position"]
                    )
                    self.game.handle_event(events.SetGameProperties(properties))
            elif d.name == "game_reset":
                self.game.handle_event(events.GameReset())
            elif d.name == "p" or d.name == "cp":
                slot = d["id"]
                user_data = d["user"]
                if user_data is not None:
                    player = self.get_player_global_data(user_data)
                    self.game.global_player_data[slot] = player
                elif slot in self.game.global_player_data:
                    del self.game.global_player_data[slot]
            elif d.name == "game_start":
                self.game.handle_event(events.GameStart())
            elif d.name == "hand":
                self.handle_hand_packet(d)
            elif d.name == "turn":
                trump = d["trump"]
                if card_index.Index.is_valid_card(trump):
                    trump = self.card_from_string(trump)
                    self.game.handle_event(events.SetTrumpCard(trump))
                elif card_index.Index.is_valid_suit(trump):
                    self.game.handle_event(events.SetTrumpSuit(const.suits.index(trump[0])))
                else:
                    log.error("handle_client_packet", "invalid trump", trump)
                self.game.validate_deck(d["deck"])
                self.game.validate_discard(d["discard"])
            elif d.name == "mode":
                modes = {int(id_): mode for id_, mode in d.items()}
                self.game.handle_event(events.SetModes(modes))
            elif d.name == "t" or d.name == "f":
                card = self.card_from_string(d["c"])
                self.game.handle_event(events.Attack(d["id"], card))
            elif d.name == "s":  # redirect
                card = self.card_from_string(d["c"])
                self.game.handle_event(events.Redirect(d["id"], card))
            elif d.name == "b":
                card_attack = self.card_from_string(d["c"])
                card_defence = self.card_from_string(d["b"])
                self.game.handle_event(events.Defence(d["id"], card_attack, card_defence))
            elif d.name == "user_info":
                player = self.get_player_global_data(d)
                pass
            elif d.name == "player_pos":
                self.game.handle_event(events.MoveSelfToPos(d["id"]))
                pass
            elif d.name == "end_turn":
                self.game.handle_event(events.EndTurn(d.get("id")))
            elif d.name == "order":
                self.game.handle_event(events.TakeFromDeckOrder(d["ids"]))

            elif d.name == "rt":
                card = self.card_from_string(d["c"])
                self.game.handle_event(events.AttackCanceled(card))
            elif d.name == "rb":
                card_attack = self.card_from_string(d["c"])
                card_defence = self.card_from_string(d["b"])
                self.game.handle_event(events.DefenceCanceled(card_attack, card_defence))
            elif d.name == "rs":
                card = self.card_from_string(d["c"])
                self.game.handle_event(events.RedirectCanceled(card))
            elif d.name == "cht":
                pass
            elif d.name == "chb":
                pass
            elif d.name == "chs":
                cards_to_players = d["c"]
                cards_to_players = {self.card_from_string(card): player_index for card, player_index in
                                    cards_to_players.items()}
                self.game.handle_event(events.ShaperBack(cards_to_players))
            elif d.name == "gd":
                pass
            elif d.name == "g":
                pass
            elif d.name == "game_over":
                self.game.handle_event(events.GameOver())
            elif d.name == "bets":
                pass
            elif d.name == "server":
                pass
            elif d.name == "features":
                pass
            elif d.name == "err":
                pass
            elif d.name == "gl":
                pass
            elif d.name == "tour":
                pass
            elif d.name == "img_msg_price":
                pass
            elif d.name == "free":
                pass
            elif d.name == "surrender":
                pass
            elif d.name == "uu":
                pass
            elif d.name == "ad_nets":
                pass
            elif d.name == "authorized":
                pass
            elif d.name == "ready_off":
                pass
            elif d.name == "btn_ready_off":
                pass
            elif d.name == "sign":
                pass
            elif d.name == "ready_on":
                pass
            elif "confirmed" in d.name:
                pass
            elif d.name == "p_off":
                pass
            elif d.name == "player_swap_request":
                pass
            elif d.name == "fl_update":
                pass
            elif d.name == "p_on":
                pass
            elif d.name == "win":
                pass
            elif d.name == "uu":
                pass
            elif d.name == "game_ready":
                pass
            elif d.name == "player_swap":
                pass
            elif d.name == "smile":
                pass
            else:
                handled = False
            if handled or not d.name:
                if self.game is not None and self.game.properties is not None:
                    pass

                if not d.name:
                    error("packet name error", name0, d)
                dicts.pop(0)
                name0 = None
            else:
                d.name = d.name[1:]

    def handle_hand_packet(self, d: NamedDict):
        hand_cards = d["cards"]
        if self.game.properties is None:
            error("handle_client_packet", "game.properties is None", d)
        hand_cards = [self.card_from_string(card) for card in hand_cards]
        self.game.handle_event(events.Hand(hand_cards))

    def get_player_global_data(self, user_info: dict):
        d = user_info
        d = GlobalPlayerData(
            id_=d["id"],
            name=d["name"],
            avatar_link=d["avatar"],
            pw=d["pw"],
            score=d["score"],
        )
        return d

    def handle_server_packet(self, bytes_):
        self.send_buf.write_bytes(bytes_)
        packet_str = self.send_buf.read_packet()
        dicts = []
        while packet_str is not None:
            d = NamedDict(packet_str)
            if d.name:
                dicts.append(d)
            packet_str = self.send_buf.read_packet()

        for d in dicts:
            if d.name == "t" or d.name == "f":
                card = self.card_from_string(d["c"])
                self.game.handle_event(events.Attack(self.game.properties.self_position, card))
            elif d.name == "b":
                card_attack = self.card_from_string(d["c"])
                card_defence = self.card_from_string(d["b"])
                self.game.handle_event(events.Defence(self.game.properties.self_position, card_attack, card_defence))
            elif d.name == "s":  # redirect
                card = self.card_from_string(d["c"])
                self.game.handle_event(events.Redirect(self.game.properties.self_position, card))
            elif d.name == "lookup_start":
                pass
            elif d.name == "lookup_stop":
                pass
            elif d.name == "join":
                pass
            elif d.name == "ready":
                pass
            elif d.name == "pass":
                pass
            elif d.name == "done":
                pass
            elif d.name == "done":
                pass
            elif d.name == "take":
                pass
            elif d.name == "give_coll_item":
                pass
            elif d.name == "cht":
                pass
            elif d.name == "chb":
                pass
            elif d.name == 'game_over':
                self.game.handle_event(events.GameOver())
            else:
                log.error("client-server packet name error", d)

    def card_from_string(self, string):
        if self.game.properties is None:
            log.error("card_from_string", "game.properties is None", string)
            return None
        else:
            return card_index.Index.from_string(string, self.game.properties.lowest_card_rank)

    def callback(self, pkt):
        src = None
        dst = None
        bytes_ = None
        try:
            if hasattr(pkt[TCP], "load"):
                src = pkt.src
                dst = pkt.dst
                bytes_ = bytes(pkt[TCP].load)
                if src == SERVER_IP:
                    self.handle_client_packet(bytes_)
                elif dst == SERVER_IP:
                    self.handle_server_packet(bytes_)
                else:
                    log.error('ДОЛБАЕБ! ПРОВЕРЬ SERVER_IP')
        except Exception as e:
            error(self.callback, traceback.format_exc(5), src=src, dst=dst, bytes_=bytes_)


if __name__ == "__main__":
    DurakSniffer().start()
    input()
