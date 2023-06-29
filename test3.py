import random

from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QPoint

class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 400)
        # Создаем QGridLayout
        self.layout = QGridLayout()

        # Создаем кнопку
        self.button = QPushButton("Изменить размер ячейки", self)
        self.button.clicked.connect(self.resizeCell)

        # Добавляем кнопку в GridLayout
        self.layout.addWidget(self.button, 0, 0)

        # Создаем виджеты и добавляем их в GridLayout
        self.widget1 = QLabel("12345678901234567890" * 5)
        self.widget1.setMouseTracking(True)
        self.widget1.installEventFilter(self)
        self.layout.addWidget(self.widget1, 1, 0, 1, 1)
        self.widget1.setStyleSheet("font-size: 100pt;")

        self.widget2 = QLabel("хуйхуйхуй")
        self.widget2.setMouseTracking(True)
        self.widget2.installEventFilter(self)
        self.layout.addWidget(self.widget2, 1, 1, 1, 1)

        self.widget3 = QLabel()
        self.widget3.setMouseTracking(True)
        self.widget3.installEventFilter(self)
        self.layout.addWidget(self.widget3, 2, 0, 1, 1)

        self.widget4 = QLabel()
        self.widget4.setMouseTracking(True)
        self.widget4.installEventFilter(self)
        self.layout.addWidget(self.widget4, 2, 1, 1, 1)

        for i in range(1, 5):
            w = getattr(self, f"widget{i}")
            w.setStyleSheet(f"background-color: #{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}")

        # Устанавливаем QGridLayout в качестве макета для виджета
        self.setLayout(self.layout)

        self.setWindowTitle('Пример')
        self.show()

    def resizeCell(self):
        # Изменение размеров ячейки по нажатию кнопки
        row = 1
        column = 1
        rowSpan = 1
        columnSpan = 2

        # Получаем указатель на виджет в выбранной ячейке
        widget = self.layout.itemAtPosition(row, column).widget()

        # Удаляем виджет из ячейки
        self.layout.removeWidget(widget)

        # Устанавливаем новые размеры ячейки для виджета
        self.layout.addWidget(widget, row, column, rowSpan, columnSpan)

    def eventFilter(self, obj, event):
        # Обработка событий мыши для изменения размеров ячеек
        if event.type() == event.MouseMove:
            if event.buttons() == Qt.LeftButton:
                # Определяем текущую позицию мыши
                currentPos = event.pos()

                # Определяем индексы ячейки, в которой находится виджет
                row, column, rowSpan, columnSpan = self.layout.getItemPosition(self.layout.indexOf(obj))

                # Определяем позицию мыши относительно виджета
                relativePos = currentPos - QPoint(obj.width(), obj.height()) / 2

                # Растягиваем ячейку по горизонтали
                if relativePos.x() > obj.width() / 2:
                    self.layout.setColumnMinimumWidth(column + columnSpan, currentPos.x())
                else:
                    self.layout.setColumnMinimumWidth(column, obj.width() - currentPos.x())

                # Растягиваем ячейку по вертикали
                if relativePos.y() > obj.height() / 2:
                    self.layout.setRowMinimumHeight(row + rowSpan, currentPos.y())
                else:
                    self.layout.setRowMinimumHeight(row, obj.height() - currentPos.y())

        return super().eventFilter(obj, event)

if __name__ == '__main__':
    app = QApplication([])
    ex = Example()
    app.exec_()