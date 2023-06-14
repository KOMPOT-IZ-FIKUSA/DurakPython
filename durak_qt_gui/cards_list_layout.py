from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QHBoxLayout

from card_index import Index
from durak_qt_gui.card_label_widget import CardLabel


class CardsListLayout(QHBoxLayout):
    def __init__(self, window):
        super().__init__(window)
        self.cards = []
        self.window = window
        self.setAlignment(Qt.AlignCenter)



    def __contains__(self, item):
        for card in self.cards:
            if isinstance(item, CardLabel):
                if card == item:
                    return True
            elif isinstance(item, Index):
                if card.card == item:
                    return True
            else:
                return False
        return False

    def add_card(self, card: Index):
        if card in self:
            return
        label = CardLabel(self.window, card, 1)
        label.setFixedSize(QSize(128, 168))

        label.enable_blue_frame()

        self.addWidget(label)
        self.cards.append(label)


