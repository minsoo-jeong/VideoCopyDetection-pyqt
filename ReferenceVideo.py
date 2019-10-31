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

from utils import *
from config import *


class ReferenceVideoTable(QWidget):
    def __init__(self, *args, **kwargs):
        super(ReferenceVideoTable, self).__init__(*args, **kwargs)
        self.videoDIR = REFERENCE_VIDEO_DIR

        self.videoExtension = ['.mp4', '.avi', '.flv']
        self.tableHeader = ["Filename", "Title", "Path", "FPS", "Duration", "Frames"]
        # filter table
        self.searchString = {"Filename": set(), "Title": set(), "Path": set()}

        self.ref_vid= self.scan_ref_vid()

        self.initUI()
        paintWidgetBackGround(self, COLOR_CONTENT)

    def initUI(self):
        mainForm = QVBoxLayout()
        mainForm.setContentsMargins(10, 10, 10, 10)
        tableForm = QHBoxLayout()

        self.initSearchBar()

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_key)
        search_layout.addWidget(self.search_line)
        search_layout.addWidget(self.search_btn)
        mainForm.addLayout(search_layout)

        self.initTable()

        self.process = QProcess()

        tableForm.addWidget(self.videoTable)
        btnGroup = QGroupBox()
        gb_layout = QVBoxLayout()

        self.addBtn = QPushButton()
        self.addBtn.setIcon(QIcon(QPixmap("./resource/icon/icons8-plus-math-48.png")))
        self.delBtn = QPushButton()
        self.delBtn.setIcon(QIcon(QPixmap("./resource/icon/icons8-minus-48.png")))
        self.delBtn.setEnabled(False)

        btnGroup.setLayout(gb_layout)
        gb_layout.addWidget(self.addBtn)
        gb_layout.addWidget(self.delBtn)
        gb_layout.setAlignment(Qt.AlignTop)

        mainForm.addLayout(tableForm)
        tableForm.addWidget(btnGroup)
        self.setLayout(mainForm)

        self.search_key.currentIndexChanged.connect(self.OnSearchKeyChanged)
        self.search_btn.clicked.connect(self.OnSearchBtnClicked)
        self.search_line.returnPressed.connect(self.OnSearchBtnClicked)
        self.search_line.textChanged.connect(self.OnSearchBtnClicked)
        self.videoTable.doubleClicked.connect(self.OnDoubleClickedRow)
        self.videoTable.clicked.connect(self.OnTableRowClicked)
        self.delBtn.clicked.connect(self.onDeleteRowBtnClicked)
        self.addBtn.clicked.connect(self.OnAddRowBtnClicked)

        self.OnSearchKeyChanged()

    def onDeleteRowBtnClicked(self):
        idx = self.videoTable.selectionModel().selectedRows()[0]

        self.model.removeRow(idx.row())

    def OnTableRowClicked(self):
        self.delBtn.setEnabled(True)

    def OnAddRowBtnClicked(self):
        fDialog = QFileDialog

        path, _ = fDialog.getOpenFileName(self)
        name = os.path.basename(path)
        title = os.path.basename(os.path.dirname(path))

        if os.path.splitext(name)[1] in self.videoExtension:
            print(name, title, path)
            self.addRow((name, title, path, "0", "0", "0"))
            self.OnSearchKeyChanged()

    def initSearchBar(self):
        self.search_line = QLineEdit()
        self.search_key = QComboBox()
        self.search_btn = QPushButton("search")
        self.searchModel = QStringListModel()
        self.completer = QCompleter()
        self.search_line.setCompleter(self.completer)

    def initTable(self):
        self.videoTable = QTableView()
        self.model = QStandardItemModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.videoTable.setModel(self.proxy)
        [self.search_key.addItem(self.tableHeader[k]) for k in range(3)]
        self.model.setColumnCount(6)
        self.model.setSortRole(Qt.UserRole)
        self.videoTable.setSortingEnabled(True)

        self.model.setHorizontalHeaderLabels(self.tableHeader)

        header = self.videoTable.horizontalHeader()


        self.videoTable.setShowGrid(False)

        self.videoTable.setSelectionBehavior(QTableView.SelectRows)
        self.videoTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.videoTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for n, (name, dt, title, fps, duration, count) in enumerate(self.ref_vid):
            self.addRow(n, (name, title, os.path.join(self.videoDIR, dt, title, name), fps, duration, count))

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        [header.setSectionResizeMode(n, QHeaderView.ResizeToContents) for n in range(3, 6)]
        # header.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name))

    def addRow(self, idx, data):
        name, title, path, fps, duration, frames = data
        self.searchString['Filename'].add(name)
        self.searchString['Title'].add(title)
        self.searchString['Path'].add(path)
        name = QStandardItem(name)
        title = QStandardItem(title)
        path = QStandardItem(path)
        fps = QStandardItem(fps)
        fps.setTextAlignment(Qt.AlignCenter)
        duration = QStandardItem(duration)
        duration.setTextAlignment(Qt.AlignCenter)
        frames = QStandardItem(frames)
        frames.setTextAlignment(Qt.AlignCenter)

        rowItems = [name, title, path, fps, duration, frames]
        color = COLOR_TABLE_1 if idx % 2 == 0 else COLOR_TABLE_2
        [i.setBackground(QBrush(color)) for i in rowItems]
        self.model.appendRow(rowItems)

    def scan_ref_vid(self):
        print('[Scan Referenece Videos] {} '.format(self.videoDIR))
        vidlist = set()

        datasets = [l for l in os.listdir(self.videoDIR) if
                    os.path.isdir(os.path.join(self.videoDIR, l)) or os.path.islink(os.path.join(self.videoDIR, l))]
        quick = [l for l in os.listdir(self.videoDIR) if l.endswith('txt')]

        for dt in datasets:
            if dt + '.txt' in quick:
                f = open(os.path.join(self.videoDIR, dt + '.txt'))
                for l in f.readlines():
                    name, title, fps, duration, count = l.rstrip().split(',')
                    featurePath = os.path.join(self.videoDIR, dt, title, os.path.splitext(name)[0] + '.pt')
                    if any(name.lower().endswith(ext) for ext in self.videoExtension) and os.path.exists(featurePath):
                        vidlist.add((name, dt, title, fps, duration, count))

        vidlist = sorted(list(vidlist), key=lambda x: x[2])
        return vidlist

    def OnDoubleClickedRow(self, idx):
        idx = idx.row()
        path = self.model.item(idx, 2).text()
        print('[DoubleClickRow] Play: {} {}'.format(path, idx))
        cmd = ['C:/Program Files (x86)/Daum/PotPlayer/PotPlayer.exe', path]

        subprocess.Popen(cmd, shell=True)

    def OnSearchKeyChanged(self):
        key = self.search_key.currentText()
        print('[Search Keyword Changed] key: {} '.format(key))
        self.searchModel.setStringList(list(self.searchString[key]))
        self.completer.setModel(self.searchModel)
        self.search_line.clear()

    def OnSearchBtnClicked(self):
        text = self.search_line.text()
        key = self.search_key.currentIndex()
        text = os.path.join(text) if key == 2 else text
        print('[Search Btn Clicked] text: {} key: {}'.format(text, key))

        self.proxy.setFilterKeyColumn(key)
        self.proxy.setFilterWildcard("*{}*".format(text) if text else "")


if __name__ == '__main__':
    from App import MyApp

    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
