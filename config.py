from PyQt5.Qt import *
from PyQt5.QtGui import *
import os

COLOR_WORKLIST = QColor(149, 117, 205)
COLOR_WORKLIST_over = QColor(209, 196, 233)
COLOR_CONTENT = QColor(250, 250, 250)
COLOR_CONTENT_2 = QColor(200, 200, 200)
COLOR_TABLE_1 = QColor(245, 245, 245)
COLOR_TABLE_2 = QColor(250, 250, 250)



BASE=os.path.dirname(os.path.abspath(__file__))
ICON_DIR=os.path.join(BASE,'resource','icon')
TMP_DIR = os.path.join(BASE,'tmp')
TMP_QUERY_DIR=os.path.join(BASE,'tmp','query')

QUERY_DIR=os.path.join(BASE,'query')

REFERENCE_VIDEO_DIR=os.path.join(BASE,'data','reference_video')

