import math
import os
import time

from PyQt5 import QtSvg
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPaintEvent, QPainter, QBrush, QColor, QFont, QPicture
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QLabel, QGraphicsProxyWidget

import const
from card_index import Index
from qt_image_loader import load_cards


class CardLabel(QLabel):
    shirt_svg_renderer = None
    shirt_svg_path = "data\\cards_svg\\shirt.svg"

    def __init__(self, window, card: Index, initial_probability: float):
        super().__init__(window)
        suit_name = const.suit_names_for_java[const.suits[card.suit_i]].lower()
        rank_name = const.ranks_value_to_string[card.absolute]
        svg_path = os.path.join("data\\cards_svg", f"{suit_name}_{rank_name}.svg")

        self.card_svg_renderer = QtSvg.QSvgRenderer(svg_path)
        if self.shirt_svg_renderer is None:
            self.shirt_svg_renderer = QtSvg.QSvgRenderer(self.shirt_svg_path)

        self._initial_y = None
        self.initial_probability = initial_probability
        self._probability = self.initial_probability
        self._left_clicked = False
        self._right_clicked = False
        self._pixmap = None


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
        super().paintEvent(a0)
        painter = QPainter(self)
        if self.probability < 0.0001:
            self.shirt_svg_renderer.render(painter)
        else:
            self.card_svg_renderer.render(painter)
            k = min(self.width(), self.height() * 168 / 128)
            width = k * 0.65
            height = k * 0.25
            font_size = k * 0.2
            rect = QRect(self.width() / 2 - width / 2, self.height() / 2 - height / 2, width, height)
            painter.fillRect(rect, QBrush(QColor("white")))
            painter.setPen(QColor("black"))
            font = QFont("Arial", font_size)
            font.setBold(True)
            painter.setFont(font)
            percentage = f"{math.floor(self.probability * 100)}%"
            painter.drawText(rect, Qt.AlignCenter, percentage)
            painter.setPen(QColor("white"))

    def enable_blue_frame(self):
        self.setStyleSheet("border: 3px solid blue;")