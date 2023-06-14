from PyQt5 import QtCore
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton

from durak_qt_gui.card_slide_animation import CardSlideAnimation
from game_data import DurakData
from durak_qt_gui.card_label_widget import CardLabel
from qt_image_loader import load_cards


class CardManagementWindow(QWidget):
    cards_images = None

    def __init__(self, min_rank, game_data: DurakData, player_pos: int):
        super().__init__()
        self.group_animation = QtCore.QParallelAnimationGroup()
        self.animation_event_filter = CardSlideAnimation(20, self.group_animation)

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
                label.installEventFilter(self)
                label.installEventFilter(self.animation_event_filter)
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
        self.show()

    def set_up_cards(self):
        pass

    def eventFilter(self, object, event):
        if isinstance(object, CardLabel):
            if event.type() == QEvent.MouseButtonRelease:
                button = event.button()
                if button == 1:
                    object.click_left()
                elif button == 2:
                    object.click_right()
        return False

    def on_confirm_button_clicked(self):
        print("Clicked")