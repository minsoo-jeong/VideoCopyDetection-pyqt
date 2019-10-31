from PyQt5.Qt import *
from PyQt5.QtGui import *
import numpy as np
import cv2

from config import *


BOLD_FONT=QFont()
BOLD_FONT.setBold(True)

def cvtMat2QPix(mat):
    tmp_cvt='./tmp/convert.png'
    cv2.imwrite(tmp_cvt,mat)
    return QPixmap(tmp_cvt)

def cvtQPix2Mat(QPix):
    tmp_cvt = './tmp/convert.png'
    QPix.save(tmp_cvt)
    return cv2.imread(tmp_cvt,cv2.IMREAD_UNCHANGED)

def paintWidgetBackGround(widget, color):
    widget.setAutoFillBackground(True)
    p = widget.palette()
    p.setColor(widget.backgroundRole(), color)
    widget.setPalette(p)

class MPanel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(MPanel, self).__init__(*args, **kwargs)
        self.setText(args[0])
        self.setFont(BOLD_FONT)

        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(70)
        # self.setFixedWidth(100)
        self.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name))

        self.select=False

    def enterEvent(self, e):
        self.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST_over.name()))

    def leaveEvent(self, e):
        if not self.select:
            self.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))


    def mousePressEvent(self, QMouseEvent):
        self.select=True
        self.clicked.emit()


if __name__ == '__main__':
    from App import MyApp
    import sys

    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())

