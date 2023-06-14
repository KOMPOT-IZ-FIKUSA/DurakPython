import math

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPaintEvent, QPainter, QBrush, QColor, QFont
from PyQt5.QtWidgets import QLabel

from durak_qt_gui.card_slide_animation import CardSlideAnimation


class CardLabel(QLabel, CardSlideAnimation):
    def __init__(self, window, suit_i: int, rank_absolute: int, loaded_cards_images: dict, shirt_pixmap,
                 initial_probability: float):
        super(CardLabel, self).__init__(window)
        self.card_pixmap = loaded_cards_images[suit_i][rank_absolute]
        self.shirt_pixmap = shirt_pixmap
        self.setPixmap(self.card_pixmap)
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
        print(self.initial_y)
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