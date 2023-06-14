import math
import random
import sys
import threading
import time
import typing
from dataclasses import dataclass
from typing import List, Tuple

import requests
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import *

import const
import events
import log
from card_index import Index
from durak_sniffer import DurakSniffer
from game_data import DurakData
from player_data import GlobalPlayerData
from qt_image_loader import load_cards

MAIN_SIZE = (1300, 900)


@dataclass
class LayoutSetting:
    columns_count: int
    rows_count: int
    setting: List[Tuple[int, int]]


PLAYERS_LAYOUT_SETTINGS = {
    2: LayoutSetting(2, 1, [(0, 0), (1, 0)]),
    3: LayoutSetting(2, 2, [(0, 0), (1, 0), (0, 1)]),
    4: LayoutSetting(2, 2, [(0, 0), (1, 0), (0, 1), (1, 1)]),
    5: LayoutSetting(3, 2, [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)]),
    6: LayoutSetting(3, 2, [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]),
}

class CardsListWidget(QWidget):
    signal = QtCore.pyqtSignal()
    class MiniCardLabel(QLabel):
        def __init__(self, window):
            super().__init__(window)
            self._initial_y = None

        @property
        def initial_y(self):
            if self._initial_y is None:
                self._initial_y = self.y()
            return self._initial_y

    def __init__(self, parent, flags, gap_width):
        if parent is None and flags is None:
            super().__init__()
        else:
            super().__init__(parent, flags)
        self.cards_indices = []
        self.cards_labels = {}
        self.setStyleSheet("background-color: #ddd;")
        self.setFixedSize(800, 800)
        self.max_distance_between_cards = gap_width + 128
        self.group_animation = QtCore.QParallelAnimationGroup()
        self.signal_handler = SignalHandler(self.signal)

        def f():
            time.sleep(3)
            for i in range(20):
                print(i)
                self.signal_handler.add(self.add_card, Index(random.randint(0, 3), random.randint(6, 14), 6))
            self.signal_handler.emit()
        #f()
        threading.Thread(target=f).start()


    def set_cards_positions(self):
        if len(self.cards_indices) == 0:
            return
        a = (self.width() - len(self.cards_indices) * 103) / (len(self.cards_indices) + 1)
        b = 103
        if a < 0:
            a = 0
            b = self.width() / len(self.cards_indices)
        for i, card in enumerate(self.cards_indices):
            card_label = self.cards_labels[card]
            card_label: QLabel
            rect = QRect(a * (i + 1) + b * i, card_label.y(), 128, 168)
            card_label.
            print(card_label.rect())

    def set_cards_pixmaps(self):
        all_pixmaps = load_cards()
        for index, label in self.cards_labels.items():
            pixmap = all_pixmaps[index.suit_i][index.absolute]
            label.setPixmap(pixmap)

    def add_card(self, card: Index):
        if card in self.cards_indices:
            return
        all_cards = load_cards()
        label = CardsListWidget.MiniCardLabel(self.window())
        label.setPixmap(all_cards[card.suit_i][card.absolute])
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(103, 144)
        label.installEventFilter(self)
        label.setStyleSheet("border: 3px solid blue;")
        self.cards_labels[card] = label
        self.cards_indices.append(card)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        self.set_cards_positions()
        self.set_cards_pixmaps()
        super().paintEvent(a0)


    def card_y_animation(self, card: MiniCardLabel, delta):
        self.animation = QPropertyAnimation(card, b'pos')
        self.animation.setDuration(600)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)
        self.animation.setEndValue(QPoint(card.x(), card.initial_y + delta))
        self.animation.start()
        return self.animation

    def eventFilter(self, object, event):
        if isinstance(object, CardsListWidget.MiniCardLabel):
            if event.type() == QEvent.Enter:
                self.group_animation.addAnimation(self.card_y_animation(object, -20))
            elif event.type() == QEvent.Leave:
                self.group_animation.addAnimation(self.card_y_animation(object, 0))
        return False


class PlayerGui:
    def __init__(self, window, player):
        self.window = window
        self.main_vertical_layout = QVBoxLayout(window)
        self.main_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.main_vertical_layout.setSpacing(0)

        self.name_and_icon_horizontal_layout = QHBoxLayout(window)

        self.name = QLabel(player.name, window)
        self.name.setStyleSheet("background-color: #ccc")
        self.name.setStyleSheet("color: #000; background-color: #ddd; font-weight: bold; font-size: 30pt")
        self.name.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.black_cards_layout = QHBoxLayout(window)
        self.red_cards_layout = QHBoxLayout(window)
        self.black_cards = {}
        self.red_cards = {}

        self.name_and_icon_horizontal_layout.addWidget(self.name)
        self.main_vertical_layout.addLayout(self.name_and_icon_horizontal_layout)
        self.main_vertical_layout.addLayout(self.black_cards_layout)
        self.main_vertical_layout.addLayout(self.red_cards_layout)

        self.avatar = QLabel()
        self.avatar.setStyleSheet("color: #000; background-color: #ddd; font-weight: bold; font-size: 30pt")
        self.avatar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.avatar.setMargin(10)
        self.name_and_icon_horizontal_layout.addWidget(self.avatar)

        def try_load_image():
            if player.avatar_link:
                try:
                    image = QImage()
                    image.loadFromData(requests.get(player.avatar_link).content)
                    pixmap = QPixmap(image)
                    self.avatar.setPixmap(pixmap.scaled(128, 128))
                except Exception as e:
                    log.error("player gui init", "try_load_image", e, player=player)

        threading.Thread(target=try_load_image).start()

    def close(self):
        self.name.deleteLater()
        self.avatar.deleteLater()
        self.black_cards_layout.deleteLater()
        self.red_cards_layout.deleteLater()
        self.name_and_icon_horizontal_layout.deleteLater()
        self.main_vertical_layout.deleteLater()

    def add_card(self, card: Index):
        if card in self.red_cards.keys() or card in self.black_cards.keys():
            return
        all_cards = load_cards()
        label = QLabel(self.window)
        label.setPixmap(all_cards[card.suit_i][card.absolute])
        label.setStyleSheet("background-color: #ddd;")
        label.setAlignment(Qt.AlignCenter)
        if card.suit_i in const.red_suits_indices:
            self.red_cards_layout.addWidget(label)
            self.red_cards[card] = label
        else:
            self.black_cards_layout.addWidget(label)
            self.black_cards[card] = label
        label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))


class SignalHandler:
    def __init__(self, true_signal):
        self.signal = true_signal
        self.args_queue = []
        self.kwargs_queue = []
        self.functions_queue = []
        self.running_stack_currently = False

        def f():
            while len(self.kwargs_queue) > 0:
                function = self.functions_queue[0]
                args = self.args_queue[0]
                kwargs = self.kwargs_queue[0]
                try:
                    function(*args, **kwargs)
                except Exception as e:
                    log.error("error in signal emit queue", e, function=function, args=args, kwargs=kwargs,
                              functions_queue_size=len(self.functions_queue))
                self.functions_queue.pop(0)
                self.args_queue.pop(0)
                self.kwargs_queue.pop(0)
            self.running_stack_currently = False

        self.signal.connect(f)

    def add(self, function, *args, **kwargs):
        self.functions_queue.append(function)
        self.args_queue.append(args)
        self.kwargs_queue.append(kwargs)

    def emit(self):
        if not self.running_stack_currently:
            self.running_stack_currently = True
            self.signal.emit()

    def wait(self):
        while len(self.functions_queue) > 0:
            pass

    def contains_function(self, function):
        for f in self.functions_queue:
            if f == function:
                return True
        return False


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


class CardLabel(QLabel):
    def __init__(self, window, suit_i: int, rank_absolute: int, loaded_cards_images: dict, shirt_pixmap,
                 initial_probability: float):
        super(CardLabel, self).__init__(window)
        self.card_pixmap = loaded_cards_images[suit_i][rank_absolute]
        self.shirt_pixmap = shirt_pixmap
        self.setPixmap(self.card_pixmap)
        self.installEventFilter(window)
        self.setAlignment(Qt.AlignCenter)
        self._initial_y = None

        self.initial_probability = initial_probability
        self._probability = self.initial_probability
        self._left_clicked = False
        self._right_clicked = False

        self._pixmap = None

        #self.setStyleSheet("border: 3px solid blue;")

    def click_left(self):
        if self._left_clicked:
            self.probability = self.initial_probability
            self._left_clicked = False
        else:
            self.probability = 1
            self._left_clicked = True
        self._right_clicked = False
        self.update()

    def click_right(self):
        if self._right_clicked:
            self.probability = self.initial_probability
            self._right_clicked = False
        else:
            self.probability = 0
            self._right_clicked = True
        self._left_clicked = False
        self.update()

    @property
    def probability(self):
        return self._probability

    @probability.setter
    def probability(self, value):
        self._probability = value

    @property
    def initial_y(self):
        if self._initial_y is None:
            self._initial_y = self.y()
        return self._initial_y

    def paintEvent(self, a0: QPaintEvent) -> None:
        # super().paintEvent(a0)
        painter = QPainter(self)
        if self.probability < 0.0001:
            painter.drawPixmap(self.rect(), self.shirt_pixmap)
        else:
            painter.drawPixmap(self.rect(), self.card_pixmap)
            rect = QRect(self.width() / 2 - 50, self.height() / 2 - 18, 100, 36)
            painter.fillRect(rect, QBrush(QColor("white")))
            painter.setPen(QColor("black"))
            font = QFont("Arial", 30)
            font.setBold(True)
            painter.setFont(font)
            percentage = f"{math.floor(self.probability * 100)}%"
            painter.drawText(rect, Qt.AlignCenter, percentage)
            painter.setPen(QColor("white"))


class CardManagementWindow(QWidget):
    cards_images = None

    def __init__(self, min_rank, game_data: DurakData, player_pos: int):
        super().__init__()
        self.game_data = game_data
        ranks_count = 15 - min_rank
        if self.cards_images is None:
            self.cards_images = load_cards()
        card_scale = list(self.cards_images[0].items())[0][1].size()

        self.setWindowTitle("Card Manager")
        self.setFixedWidth(136 * ranks_count)
        self.setFixedHeight(800)
        self.main_vertical_layout = QVBoxLayout(self)
        self.grid_layout = QGridLayout(self)
        probs_array = game_data.players[player_pos].probs_container.probs
        self.cards_labels = {}
        for suit_index in range(4):
            self.cards_labels[suit_index] = {}
            for rank_index in range(ranks_count):
                rank_value = rank_index + min_rank
                probability = probs_array[suit_index, rank_index]
                label = CardLabel(self, suit_index, rank_value, self.cards_images,
                                  self.cards_images["shirt"].scaled(card_scale), probability)
                self.cards_labels[suit_index][rank_value] = label
                self.grid_layout.addWidget(label, suit_index, rank_index)

        self.horizontal_layout = QHBoxLayout(self)

        self.main_vertical_layout.addLayout(self.grid_layout)
        self.main_vertical_layout.addLayout(self.horizontal_layout)
        self.confirm_button = QPushButton(self)
        self.confirm_button.setFixedHeight(64)
        self.confirm_button.setStyleSheet("font-size: 32px; font-weight: bold;")
        self.confirm_button.setText("OK")
        self.confirm_button.clicked.connect(self.on_confirm_button_clicked)
        self.main_vertical_layout.addWidget(self.confirm_button)
        self.setLayout(self.main_vertical_layout)
        self.group_animation = QtCore.QParallelAnimationGroup()
        self.show()

    def card_y_animation(self, card: CardLabel, delta):
        self.animation = QPropertyAnimation(card, b'pos')
        self.animation.setDuration(600)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)
        self.animation.setEndValue(QPoint(card.x(), card.initial_y + delta))
        self.animation.start()
        return self.animation

    def eventFilter(self, object, event):
        if isinstance(object, CardLabel):
            if event.type() == QEvent.Enter:
                self.group_animation.addAnimation(self.card_y_animation(object, -20))
            elif event.type() == QEvent.Leave:
                self.group_animation.addAnimation(self.card_y_animation(object, 0))
            elif event.type() == QEvent.MouseButtonRelease:
                button = event.button()
                if button == 1:
                    object.click_left()
                elif button == 2:
                    object.click_right()
        return False

    def on_confirm_button_clicked(self):
        print("Clicked")

def test_card_manager():
    app = QApplication([])
    game_data = DurakData(2, 6)
    for i in range(6):
        game_data.move_card_from_deck_to_player(0)
        game_data.move_card_from_deck_to_player(1)

    c = CardManagementWindow(6, game_data, 0)
    sys.exit(app.exec_())


if __name__ == "__main__":
    #test_card_manager()

    app = QApplication([])
    #w = MainWindow()
    t = CardsListWidget(None, None, 2)
    #t.add_card(Index(0, 6, 6))
    #t.add_card(Index(0, 7, 6))
    #t.add_card(Index(0, 8, 6))
    #t.add_card(Index(3, 13, 6))

    t.show()
    sys.exit(app.exec_())
