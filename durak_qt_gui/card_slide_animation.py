from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QEvent


class CardSlideAnimation:

    def __init__(self, delta, group_animation):
        self.delta = delta
        self.group_animation = group_animation

    def _card_y_animation(self, card, delta):
        self.animation = QPropertyAnimation(card, b'pos')
        self.animation.setDuration(600)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)
        self.animation.setEndValue(QPoint(card.x(), card.initial_y + delta))
        self.animation.start()
        return self.animation

    def eventFilter(self, object, event):
        assert hasattr(object, "initial_y")
        if event.type() == QEvent.Enter:
            self.group_animation.addAnimation(self._card_y_animation(object, -self.delta))
        elif event.type() == QEvent.Leave:
            self.group_animation.addAnimation(self._card_y_animation(object, 0))
        return False