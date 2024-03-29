from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QEvent, QObject


class CardSlideAnimation(QObject):

    def __init__(self, window, delta, group_animation):
        super().__init__(window)
        self.delta = delta
        self.group_animation = group_animation

    def _card_y_animation(self, card, delta):
        self.animation = QPropertyAnimation(card, b'pos')
        self.animation.setDuration(600)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)
        self.animation.setEndValue(QPoint(card.x(), card.initial_y + delta))
        self.animation.start(self.animation.DeleteWhenStopped)
        return self.animation

    def eventFilter(self, object, event):
        if event.type() == QEvent.Enter:
            self.group_animation.addAnimation(self._card_y_animation(object, -self.delta))
        elif event.type() == QEvent.Leave:
            self.group_animation.addAnimation(self._card_y_animation(object, 0))
        return False

