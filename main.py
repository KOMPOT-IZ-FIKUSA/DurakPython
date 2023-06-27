import sys

from PyQt5 import QtGui
from PyQt5.Qt import *

from durak_qt_gui.main_window import DurakMainWindow

from const import logo_path

if __name__ == "__main__":

    app = QApplication([])
    app.setWindowIcon(QtGui.QIcon(logo_path))

    MainWindow = DurakMainWindow()
    sys.exit(app.exec_())
