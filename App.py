import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
import subprocess
import shutil
import cv2
import numpy as np
import time

from ReferenceVideo import ReferenceVideoTable
from VideoEditor import VideoEditor
from CopyDetector import CopyDetector
from utils import *
from config import *





class MyApp(QWidget):

    def __init__(self, *args, **kwargs):
        super(MyApp, self).__init__(*args, **kwargs)


        self.copyDetector=CopyDetector()
        self.referenceVideo=ReferenceVideoTable()
        self.videoEditor=VideoEditor()

        #link
        self.copyDetector.referenceVideo=self.referenceVideo.ref_vid

        self.tabs = QTabWidget()
        self.tabs.addTab(self.copyDetector, 'CopyDetect')
        self.tabs.addTab(self.referenceVideo, 'ReferenceVideo')
        self.tabs.addTab(self.videoEditor, 'VideoEdit')
        self.tabs.tabBar().hide()
        self.tabs.setContentsMargins(0, 0, 0, 0)


        # self.tabs.setStyleSheet('border:1px')

        self.initUI()
        self.btn_main.enterEvent(QEvent(QEvent.Enter))

    def initUI(self):
        self.setWindowTitle('My First Application')
        self.move(200, 200)
        self.resize(1600, 800)
        mainForm = QHBoxLayout()
        mainForm.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainForm)

        left = QGroupBox()
        left_layout = QVBoxLayout()
        left.setLayout(left_layout)

        left_layout.setAlignment(Qt.AlignTop)
        left_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.btn_main = MPanel('CopyDetect')
        self.btn_ref = MPanel('ReferenceVideo')
        self.btn_edit = MPanel('VideoEdit')

        left_layout.addWidget(self.btn_main)
        left_layout.addWidget(self.btn_ref)
        left_layout.addWidget(self.btn_edit)
        self.right = self.tabs

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(self.right)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([200, 1000])
        paintWidgetBackGround(splitter, COLOR_CONTENT)
        # splitter.setStyleSheet('border:1px')
        mainForm.addWidget(splitter)
        '''
        mainForm.addWidget(left)
        mainForm.addWidget(self.right)
        '''

        paintWidgetBackGround(left, COLOR_WORKLIST)

        # event Listener
        self.btn_main.clicked.connect(self.onMainBtnClick)
        self.btn_ref.clicked.connect(self.onRefBtnClick)
        self.btn_edit.clicked.connect(self.onEditBtnClick)

    def onMainBtnClick(self):
        sender = self.sender()
        self.tabs.setCurrentIndex(0)

        self.btn_ref.select = False
        self.btn_ref.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))
        self.btn_edit.select = False
        self.btn_edit.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))
        # QMessageBox.about(self, "message", "{} clicked".format(sender.text()))

    def onRefBtnClick(self):
        sender = self.sender()
        self.tabs.setCurrentIndex(1)
        self.btn_main.select = False
        self.btn_main.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))
        self.btn_edit.select = False
        self.btn_edit.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))

        # QMessageBox.about(self, "message", "{} clicked".format(sender.text()))

    def onEditBtnClick(self):
        sender = self.sender()
        self.tabs.setCurrentIndex(2)
        self.btn_main.select=False
        self.btn_main.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))
        self.btn_ref.select=False
        self.btn_ref.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))

        # QMessageBox.about(self, "message", "{} clicked".format(sender.text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
