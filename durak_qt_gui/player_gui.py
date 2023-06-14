import threading

import requests
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy

import const
import log
from card_index import Index
from qt_image_loader import load_cards


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