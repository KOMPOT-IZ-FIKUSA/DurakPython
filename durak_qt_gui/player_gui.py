import threading

import requests
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget

import const
import log
from card_index import Index
from durak_qt_gui.cards_list_layout import CardsListLayout
from durak_qt_gui.signal_handler import SignalHandler
from qt_image_loader import load_cards


class PlayerGui:
    def __init__(self, window, player, enter_card_edit_mode, signal_handler):
        self.container = QLabel()
        self.container.setStyleSheet("background-color: #ccc")

        self.window = window
        self.main_vertical_layout = QVBoxLayout(self.container)
        self.main_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.main_vertical_layout.setSpacing(0)

        self.name_and_icon_horizontal_layout = QHBoxLayout(window)

        self.name = QLabel(player.name, window)
        self.name.setStyleSheet("color: #000; font-weight: bold; font-size: 30pt")
        self.name.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.black_cards = CardsListLayout(window)
        self.red_cards = CardsListLayout(window)

        self.name_and_icon_horizontal_layout.addWidget(self.name)
        self.main_vertical_layout.addLayout(self.name_and_icon_horizontal_layout)
        self.main_vertical_layout.addLayout(self.black_cards)
        self.main_vertical_layout.addLayout(self.red_cards)
        self.main_vertical_layout.setStretch(0, 1)
        self.main_vertical_layout.setStretch(1, 2)
        self.main_vertical_layout.setStretch(2, 2)

        self.avatar = None

        def init_avatar_label(pixmap):
            self.avatar = QLabel()
            self.avatar.setStyleSheet("color: #000; font-weight: bold; font-size: 30pt")
            self.avatar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.avatar.setMargin(10)
            self.name_and_icon_horizontal_layout.addWidget(self.avatar)
            self.avatar.setPixmap(pixmap.scaled(64, 64))

        def try_load_image():
            if player.avatar_link:
                try:
                    image = QImage()
                    image.loadFromData(requests.get(player.avatar_link).content)
                    pixmap = QPixmap(image)
                    signal_handler.add(init_avatar_label, pixmap)
                    signal_handler.emit()
                except Exception as e:
                    log.error("player gui init", "try_load_image", e, player=player)

        threading.Thread(target=try_load_image).start()

        self.management_window: QWidget = None

        def call_cards_management_safely(a0):
            if self.management_window is None:
                self.management_window = enter_card_edit_mode()
                self.management_window.show()

                def on_close(a0):
                    self.management_window = None

                self.management_window.closeEvent = on_close

        self.container.mouseReleaseEvent = call_cards_management_safely

    def close(self):
        if self.avatar is not None:
            self.avatar.deleteLater()
        self.name.deleteLater()
        self.red_cards.deleteLater()
        self.black_cards.deleteLater()
        self.name_and_icon_horizontal_layout.deleteLater()
        self.container.deleteLater()
        self.main_vertical_layout.deleteLater()

    def add_card(self, card: Index):
        if card.suit_i in const.red_suits_indices:
            self.red_cards.add_card(card)
        else:
            self.black_cards.add_card(card)
