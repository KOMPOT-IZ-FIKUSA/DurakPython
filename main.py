import sys

from PyQt5.Qt import *

from card_index import Index
from durak_qt_gui.card_label_widget import CardLabel
from durak_qt_gui.card_management_window import CardManagementWindow
from durak_qt_gui.cards_list_layout import CardsListLayout
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
            self.setFixedSize(256, 256)
            self.cards_layout = QGridLayout(self)
            self.setLayout(self.cards_layout)
            self.cards_layout.addWidget(CardLabel(self, Index(0, 6, 6), 1), 0, 0)
            # self.cards_layout.add_card(Index(0, 6, 6))
            # self.cards_layout.add_card(Index(1, 6, 6))
            # self.cards_layout.add_card(Index(2, 6, 6))
            # self.cards_layout.add_card(Index(3, 6, 6))
            self.show()

    app = QApplication([])
    c = TestWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_cards_layout()

    app = QApplication([])
    #w = MainWindow()
    t = CardsListLayout(None, None, 2)
    #t.add_card(Index(0, 6, 6))
    #t.add_card(Index(0, 7, 6))
    #t.add_card(Index(0, 8, 6))
    #t.add_card(Index(3, 13, 6))

    t.show()
    sys.exit(app.exec_())
