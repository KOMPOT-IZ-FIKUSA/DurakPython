from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize, QParallelAnimationGroup, QRect
from PyQt5.QtWidgets import QHBoxLayout, QSizePolicy

import log
from card_index import Index
from durak_qt_gui.card_label_widget import CardLabel
from durak_qt_gui.card_slide_animation import CardSlideAnimation


class CardsListLayout(QHBoxLayout):
    def __init__(self, window):
        super().__init__(window)
        self.cards = []
        self.window = window
        self.setAlignment(Qt.AlignCenter)
        self.setSpacing(0)
        self.setContentsMargins(0, 0, 40, 0)
        self.group_animation = QParallelAnimationGroup()
        self.animation_event_filter = CardSlideAnimation(self, 20, self.group_animation)

        self.size_policy = None

    def set_cards_size_policy(self, w, h):
        self.size_policy = (w, h)
        for card in self.cards:
            card.setSizePolicy(card)

    def __contains__(self, item):
        for card in self.cards:
            if isinstance(item, CardLabel):
                if card.card == item.card:
                    return True
            elif isinstance(item, Index):
                if card.card == item:
                    return True
            else:
                return False
        return False

    def fix_cards_proportions(self):
        for card in self.cards:
            card.setFixedWidth(card.height() * 128/168)


    def setGeometry(self, a0: QtCore.QRect) -> None:
        self.fix_cards_proportions()
        super().setGeometry(a0)

    def update(self) -> None:
        self.fix_cards_proportions()
        super().update()

    def add_card(self, card: Index, side="left"):
        if card in self:
            return
        label = CardLabel(self.window, card, 1)
        if self.size_policy is not None:
            label.setSizePolicy(*self.size_policy)
        label.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        self.group_animation.stop()

        label.installEventFilter(self.animation_event_filter)
        if side == "right":
            self.addWidget(label)
            self.cards.append(label)
        elif side == "left":
            self.addWidget(label)
            self.cards.insert(0, label)
        else:
            log.error("cards_list_layout", "add_card", "invalid side", side=side)

    def remove_card(self, card: Index):
        if card not in self:
            return
        for card_label in self.cards:
            card_label: CardLabel
            if card_label.card == card:
                break
        self.cards.remove(card_label)
        card_label.setParent(None)
        card_label.deleteLater()
        self.removeWidget(card_label)


    def set_cards(self, cards: List[Index]):
        for card in cards:
            if len(self.cards) == 0 or self.cards[0].card.suit_i == card.suit_i:
                self.add_card(card, "left")
            else:
                self.add_card(card, "right")
        to_remove = []
        for label in self.cards:
            if label.card not in cards:
                to_remove.append(label.card)
        for card in to_remove:
            self.remove_card(card)
        self.fix_cards_proportions()