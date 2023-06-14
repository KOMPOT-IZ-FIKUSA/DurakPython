from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QEvent
from PyQt5.QtWidgets import QLayout

from card_index import Index
from durak_qt_gui.signal_handler import SignalHandler
from qt_image_loader import load_cards


class CardsListLayout(QLayout):
    pass