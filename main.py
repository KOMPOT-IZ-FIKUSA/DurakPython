import sys

from PyQt5.Qt import *

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

    c = CardManagementWindow(6, game_data, 0)
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_card_manager()

    app = QApplication([])
    #w = MainWindow()
    t = CardsListLayout(None, None, 2)
    #t.add_card(Index(0, 6, 6))
    #t.add_card(Index(0, 7, 6))
    #t.add_card(Index(0, 8, 6))
    #t.add_card(Index(3, 13, 6))

    t.show()
    sys.exit(app.exec_())
