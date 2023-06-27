import threading
import time

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QMovie, QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel

import const
import events
from card_index import Index
from durak_qt_gui.card_management_window import CardManagementWindow
from durak_qt_gui.player_gui import PlayerGui
from durak_qt_gui.players_layout_setting import PLAYERS_LAYOUT_SETTINGS
from durak_qt_gui.signal_handler import SignalHandler
from durak_sniffer import DurakSniffer
from game_properties import GameProperties
from player_data import GlobalPlayerData


class DurakMainWindow(QWidget):
    signal = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Durak Cheat")
        self.setWindowIcon(QtGui.QIcon(const.logo_path))
        self.setFixedSize(QtCore.QSize(1300, 1000))
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(20)

        self.setup_boot_gui()

        self.signal_handler = SignalHandler(self.signal)

        self.player_guis = {}

        self.sniffer = DurakSniffer()
        self.sniffer.game.add_event_handler(self.on_game_event)

        self.last_cards_set_time = 0

        #self.sniffer.game.handle_event(events.SetGameProperties(GameProperties(0, 0, 0, 0, 0, 2, 6, 100, 0)))
        #self.sniffer.game.global_player_data[0] = GlobalPlayerData(123, "Лёха", 1, 1, 'https://i.pinimg.com/originals/8a/de/fe/8adefe5af862b4f9cec286c6ee4722cb.jpg')
        #self.sniffer.game.global_player_data[1] = GlobalPlayerData(456, "Гоха", 1, 1, None)
        #self.sniffer.game.handle_event(events.GameStart())
        #self.sniffer.game.handle_event(events.TakeFromDeckOrder([0, 0, 1]))
        #self.sniffer.game.handle_event(events.Hand([
        #  Index(0, 9, 6),
        #  Index(0, 8, 6),
        #]))

        #def f():
        #    time.sleep(5)
        #    self.sniffer.game.handle_event(events.GameOver())

        #threading.Thread(target=f).start()

        self.show()
        self.sniffer.start()

    def setup_boot_gui(self):
        self.background_rect = QLabel("", self)
        self.background_rect.setFixedSize(self.size())
        self.background_rect.setStyleSheet("background-color: #FFFFFF")

        self.loading_animation_label = QLabel(self)
        self.loading_animation_label.setGeometry(0, 0, 200, 200)

        self.animation_movie = QMovie("data\\анимация_загрузки.gif")
        self.loading_animation_label.setMovie(self.animation_movie)

        self.animation_movie.start()

        self.text_label = QLabel('Ожидание начала игры', self)
        self.text_label.setFont(QFont('Arial', 30))

        self.text_label.setGeometry(0, 0, 500, 100)

        self.text_label.move(
            (
                    self.size().width() // 2) - self.text_label.size().width() // 2 + self.loading_animation_label.size().width() // 2,
            (self.size().height() // 2) - self.text_label.size().height())
        self.loading_animation_label.move(
            (
                    self.size().width() // 2) - self.loading_animation_label.size().width() // 2 - self.text_label.size().width() // 2,
            (self.size().height() // 2) - (self.loading_animation_label.size().height() // 2) - 50)

        self.setLayout(self.grid_layout)

        self.main_background_rect = QLabel("", self)
        self.main_background_rect.setFixedSize(self.size())

        self.hide_boot_gui(False)

    def hide_boot_gui(self, delete_later):
        if not delete_later:
            self.main_background_rect.setStyleSheet("background-color: transparent;")
        else:
            self.main_background_rect.setStyleSheet("background-color: #000;")

    def create_player_gui(self, column, row, player_pos, player: GlobalPlayerData):

        self.hide_boot_gui(True)
        def call_management_window():
            w = CardManagementWindow(self.sniffer.game.data, player_pos)
            w.show()
            return w

        gui = PlayerGui(self, player, call_management_window, self.signal_handler)
        pos = (column, row)
        self.grid_layout.addWidget(gui.container, row, column)
        self.player_guis[pos] = gui
        self.grid_layout.setColumnStretch(column, 1000)
        self.grid_layout.setRowStretch(row, 1000)
        return gui

    def close_all_player_guis(self):
        self.hide_boot_gui(False)
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
                self.signal_handler.add(self.create_player_gui, column, row, player_index, player_data)
            self.signal_handler.emit()
        if isinstance(event, events.GameOver):
            self.signal_handler.add(self.close_all_player_guis)
            self.signal_handler.emit()

        self.set_cards_safely()

    def set_cards_safely(self):
        if not self.sniffer.game.game_running():
            return
        if self.last_cards_set_time + 1 > time.perf_counter():
            return
        if len(self.player_guis.keys()) != self.sniffer.game.properties.players_count:
            return
        if not self.signal_handler.contains_function(self.set_cards_unsafely):
            self.signal_handler.add(self.set_cards_unsafely)
            self.signal_handler.emit()
            self.last_cards_set_time = time.perf_counter()

    def set_cards_unsafely(self):
        game = self.sniffer.game
        if game.game_running():
            players_count = game.properties.players_count
            min_rank = game.properties.lowest_card_rank
            ranks_count = 15 - min_rank
            for player_index in range(game.properties.players_count):
                player_cards_container = game.data.players[player_index].probs_container
                red_cards = []
                black_cards = []
                for suit_index, suit in enumerate(const.suits):
                    cards = [Index(suit_index, i + min_rank, min_rank) for i in range(ranks_count) if
                             player_cards_container.probs[suit_index, i] > 0.9999]
                    if suit_index in const.red_suits_indices:
                        red_cards += cards
                    else:
                        black_cards += cards

                setting = PLAYERS_LAYOUT_SETTINGS[players_count]
                gui = self.player_guis[setting.setting[player_index]]
                gui.red_cards.set_cards(red_cards)
                gui.black_cards.set_cards(black_cards)

        def f():
            time.sleep(1)
            if self.sniffer.game.game_running():
                self.signal_handler.add(self.set_cards_unsafely)
                self.signal_handler.emit()

        threading.Thread(target=f).start()


