import random
import sys

from PyQt5.Qt import *

from card_index import Index
from durak_qt_gui.card_label_widget import CardLabel
from durak_qt_gui.card_management_window import CardManagementWindow
from durak_qt_gui.cards_list_layout import CardsListLayout
from durak_qt_gui.main_window import DurakMainWindow
from game_data import DurakData

MAIN_SIZE = (1300, 900)


def test_card_manager():
    app = QApplication([])
    game_data = DurakData(2, 6)
    for i in range(6):
        game_data.move_card_from_deck_to_player(0)
        game_data.move_card_from_deck_to_player(1)
    game_data.set_probability(game_data.players[0].probs_container, Index(0, 6, 6), 0)

    c = CardManagementWindow(6, game_data, 0)
    sys.exit(app.exec_())


def test_cards_layout():
    class TestWindow(QWidget):
        def __init__(self):
            super().__init__()

            self.cards_layout = CardsListLayout(self)
            self.setLayout(self.cards_layout)
            w = 128 * 4
            h = 168 * 4
            #self.setFixedSize(w, h)


            self.cards_layout.add_card(Index(0, 6, 6))
            self.cards_layout.add_card(Index(1, 6, 6))
            self.cards_layout.add_card(Index(0, 7, 6))
            self.cards_layout.add_card(Index(1, 7, 6))
            button = QPushButton()
            self.cards_layout.addWidget(button)
            def f():
                self.cards_layout.add_card(Index(random.randint(0, 3), random.randint(2, 14), 6))
            button.clicked.connect(f)

            # self.cards_layout.add_card(Index(0, 6, 6))
            # self.cards_layout.add_card(Index(1, 6, 6))
            # self.cards_layout.add_card(Index(2, 6, 6))
            # self.cards_layout.add_card(Index(3, 6, 6))
            self.show()

    app = QApplication([])
    c = TestWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":

    #test_cards_layout()


    app = QApplication([])
    w = DurakMainWindow()
    sys.exit(app.exec_())
