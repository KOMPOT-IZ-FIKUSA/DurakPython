import time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QGridLayout

import const
import events
from card_index import Index
from durak_sniffer import DurakSniffer
from durak_qt_gui.players_layout_setting import PLAYERS_LAYOUT_SETTINGS
from durak_qt_gui.player_gui import PlayerGui
from durak_qt_gui.signal_handler import SignalHandler
from player_data import GlobalPlayerData


class MainWindow(QWidget):
    signal = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Durak Cheat")
        self.setFixedSize(QtCore.QSize(1300, 1000))
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(20)
        self.setLayout(self.grid_layout)

        backround_rect = QtWidgets.QLabel("", self)
        backround_rect.setFixedSize(self.size())
        backround_rect.setStyleSheet("background-color: #000")

        self.signal_handler = SignalHandler(self.signal)

        self.player_guis = {}

        self.sniffer = DurakSniffer()
        self.sniffer.game.add_event_handler(self.on_game_event)

        for pos in PLAYERS_LAYOUT_SETTINGS[6].setting:
            player = self.create_player_gui(*pos, GlobalPlayerData(0, "Player", 0, 0, None))
            player.add_card(Index(0, 6, 6))
            player.add_card(Index(1, 6, 6))
            player.add_card(Index(2, 6, 6))
            player.add_card(Index(3, 6, 6))
            player.add_card(Index(2, 7, 6))
            player.add_card(Index(3, 7, 6))
            player.add_card(Index(3, 8, 6))
            player.add_card(Index(3, 9, 6))
            player.add_card(Index(3, 10, 6))


        self.show()
        self.sniffer.start()

        self.last_cards_set_time = 0

    def create_player_gui(self, column, row, player: GlobalPlayerData):
        gui = PlayerGui(self, player)
        pos = (column, row)
        self.grid_layout.addLayout(gui.main_vertical_layout, row, column)
        self.player_guis[pos] = gui
        return gui

    def close_all_player_guis(self):
        for p in self.player_guis.values():
            p.close()
            p: PlayerGui
        self.player_guis.clear()

    def on_game_event(self, event):
        if isinstance(event, events.GameStart):
            players_count = self.sniffer.game.properties.players_count
            setting = PLAYERS_LAYOUT_SETTINGS[players_count]
            self.signal_handler.add(self.close_all_player_guis)
            for player_index in range(players_count):
                column, row = setting.setting[player_index]
                player_data: GlobalPlayerData = self.sniffer.game.global_player_data[player_index]
                self.signal_handler.add(self.create_player_gui, column, row, player_data)
            self.signal_handler.emit()

        self.set_cards_safely()

    def set_cards_safely(self):
        if self.last_cards_set_time + 1 > time.perf_counter():
            return
        self.last_cards_set_time = time.perf_counter()
        if not self.sniffer.game.game_running():
            return
        if len(self.player_guis.keys()) != self.sniffer.game.properties.players_count:
            return
        if not self.signal_handler.contains_function(self.set_cards_unsafely):
            self.signal_handler.add(self.set_cards_unsafely)
            self.signal_handler.emit()

    def set_cards_unsafely(self):
        game = self.sniffer.game
        if game.game_running():
            players_count = game.properties.players_count
            min_rank = game.properties.lowest_card_rank
            ranks_count = 15 - min_rank
            for player_index in range(game.properties.players_count):
                player_cards_container = game.data.players[player_index].probs_container
                red_cards_strings = []
                black_cards_strings = []
                for suit_index, suit in enumerate(const.suits):
                    ranks = [min_rank + i for i in range(ranks_count) if
                             player_cards_container.probs[suit_index, i] > 0.9999]
                    ranks.sort()
                    cards_strings = [const.ranks_value_to_string[rank] + suit for rank in ranks]
                    red = "♥♦"
                    if suit in red:
                        red_cards_strings += cards_strings
                    else:
                        black_cards_strings += cards_strings

                def compose_cards_to_final_string(cards_strings):
                    res = ""
                    for i, c in enumerate(cards_strings):
                        if i % 6 == 0 and i != 0:
                            res += "\n"
                        res += " " + c
                    return res

                red_cards_final_string = compose_cards_to_final_string(red_cards_strings)
                black_cards_final_string = compose_cards_to_final_string(black_cards_strings)
                setting = PLAYERS_LAYOUT_SETTINGS[players_count]
                gui = self.player_guis[setting.setting[player_index]]
                gui.red_cards.setText(red_cards_final_string)
                gui.black_cards.setText(black_cards_final_string)