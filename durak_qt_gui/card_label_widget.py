import math

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPaintEvent, QPainter, QBrush, QColor, QFont
from PyQt5.QtWidgets import QLabel

from card_index import Index
from qt_image_loader import load_cards


class CardLabel(QLabel):
    cards_images = None

    def __init__(self, window, card: Index, initial_probability: float):
        super(CardLabel, self).__init__(window)
        if self.cards_images is None:
            self.cards_images = load_cards()

        self.card = card
        self.card_pixmap = self.cards_images[card.suit_i][card.absolute]
        self.shirt_pixmap = self.cards_images["shirt"]
        self.setAlignment(Qt.AlignCenter)
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
            painter.drawPixmap(self.rect(), self.shirt_pixmap)
        else:
            painter.drawPixmap(self.rect(), self.card_pixmap)

            k = min(self.width(), self.height() * 168 / 128)
            width = k * 0.6
            height = k * 0.2
            font_size = k / 6
            print(k)
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