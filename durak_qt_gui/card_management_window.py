import logging

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton

import log
from card_index import Index
from durak_qt_gui import card_label_widget
from durak_qt_gui.card_slide_animation import CardSlideAnimation
from game_data import DurakData
from durak_qt_gui.card_label_widget import CardLabel


class CardManagementWindow(QWidget):

    def __init__(self, game_data: DurakData, player_pos: int):
        super().__init__()
        self.game_data = game_data
        self.player_pos = player_pos
        self.min_rank = game_data.get_min_card_rank()
        ranks_count = 15 - self.min_rank
        self.card_scale = (128, 168)
        self.group_animation = QtCore.QParallelAnimationGroup()
        self.animation_event_filter = CardSlideAnimation(self, 20, self.group_animation)
        self.ranks_count = ranks_count

        self.set_up_layouts()
        self.cards_labels = {}
        self.set_up_cards(game_data.players[player_pos].probs_container.probs)

        self.show()

    def set_card_background_to_green_if_selected(self, label: CardLabel):
        if label.selected:
            label.custom_background = card_label_widget.BackgroundColor.GREEN
        else:
            label.custom_background = card_label_widget.BackgroundColor.NONE

    def set_up_layouts(self):
        self.setWindowTitle("Card Manager")
        self.setFixedWidth(136 * self.ranks_count)
        self.setFixedHeight(800)
        self.main_vertical_layout = QVBoxLayout(self)
        self.grid_layout = QGridLayout(self)
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

    def set_up_cards(self, probs_array):
        for suit_index in range(4):
            self.cards_labels[suit_index] = {}
            for rank_index in range(self.ranks_count):
                rank_value = rank_index + self.min_rank
                card = Index(suit_index, rank_value, self.min_rank)
                probability = probs_array[suit_index, rank_index]
                label = CardLabel(self, card, probability)
                label.installEventFilter(self)
                label.installEventFilter(self.animation_event_filter)
                self.cards_labels[suit_index][rank_value] = label
                self.grid_layout.addWidget(label, suit_index, rank_index)


    def eventFilter(self, object, event):
        if isinstance(object, CardLabel):
            if event.type() == QEvent.MouseButtonRelease:
                button = event.button()
                if button == 1:
                    object.click_left()
                elif button == 2:
                    object.click_right()
                self.set_card_background_to_green_if_selected(object)
        return False


    def on_confirm_button_clicked(self):
        probs = self.game_data.players[self.player_pos].probs_container
        changes_queue = []
        for suit_index, ranks in self.cards_labels.items():
            for rank_index, label in ranks.items():
                if label.selected and abs(probs.get(label.card) - label.probability) > 0.0001:
                    changes_queue.append([label.card, label.probability])
        for index, value in changes_queue:
            try:
                self.game_data.set_probability(probs, index, value)
            except Exception as e:
                log.error(e, "CardManager", "on_confirm_button_clicked", index=index)
        self.close()