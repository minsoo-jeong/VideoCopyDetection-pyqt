import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
import subprocess


class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        QSortFilterProxyModel.__init__(self, *args, **kwargs)
        self.filters = {}

    def setFilterByColumn(self, regex, column):
        self.filters[column] = regex
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        for key, regex in self.filters.items():
            ix = self.sourceModel().index(source_row, key, source_parent)
            if ix.isValid():
                text = self.sourceModel().data(ix).toString()
                if not text.contains(regex):
                    return False
        return True


class ReferenceVideoTable(QWidget):
    def __init__(self):
        super().__init__()
        self.root = os.path.abspath('./data')
        '''
        make symbolic link for Windows
        mklink /D "core_dataset_video" "D:\copydetection-app-data\core_dataset\videos\core_dataset\videos"
        '''

        self.ref_vid = self.scan_ref_vid()
        self.tableHeader = ["filename", "title", "path", "FPS", "Duration", "Frames"]

        # filter table
        self.searchString = {"filename": set(), "title": set(), "path": set()}
        self.videoExtension = ['.mp4', '.avi', '.flv']

        self.initUI()

    def initUI(self):
        mainForm = QHBoxLayout()
        tableForm = QVBoxLayout()

        self.initSearchBar()

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_key)
        search_layout.addWidget(self.search_line)
        search_layout.addWidget(self.search_btn)

        self.initTable()

        tableForm.addLayout(search_layout)
        tableForm.addWidget(self.videoTable)

        self.process = QProcess()

        btnGroup = QGroupBox()
        gb_layout = QVBoxLayout()
        btnGroup.setLayout(gb_layout)

        self.addBtn = QPushButton("add")

        self.delBtn = QPushButton("del")
        self.delBtn.setEnabled(False)

        gb_layout.addWidget(self.addBtn)
        gb_layout.addWidget(self.delBtn)
        gb_layout.setAlignment(Qt.AlignTop)

        mainForm.addLayout(tableForm)
        mainForm.addWidget(btnGroup)
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
        idx=self.videoTable.selectionModel().selectedRows()[0]

        self.model.removeRow(idx.row())


    def OnTableRowClicked(self):
        self.delBtn.setEnabled(True)

    def OnAddRowBtnClicked(self):
        fDialog=QFileDialog
        
        path,_= fDialog.getOpenFileName(self)
        name=os.path.basename(path)
        title=os.path.basename(os.path.dirname(path))

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
        self.videoTable.setSortingEnabled(True)

        self.model.setHorizontalHeaderLabels(self.tableHeader)

        header = self.videoTable.horizontalHeader()

        self.videoTable.setSelectionBehavior(QTableView.SelectRows)
        self.videoTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.videoTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for n, (path, name) in enumerate(self.ref_vid):
            self.addRow((name, os.path.basename(path), path, "0", "0", "0"))

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        [header.setSectionResizeMode(n, QHeaderView.Stretch) for n in range(1, 6)]

    def addRow(self, data):
        name, title, path, fps, duration, frames = data
        self.searchString['filename'].add(name)
        self.searchString['title'].add(title)
        self.searchString['path'].add(path)
        name = QStandardItem(name)
        title = QStandardItem(title)
        path = QStandardItem(path)
        fps = QStandardItem(fps)
        fps.setTextAlignment(Qt.AlignCenter)
        duration = QStandardItem(duration)
        duration.setTextAlignment(Qt.AlignCenter)
        frames = QStandardItem(frames)
        frames.setTextAlignment(Qt.AlignCenter)

        self.model.appendRow([name, title, path, fps, duration, frames])

    def scan_ref_vid(self):
        vidlist = []
        for base, dir, files in os.walk(self.root, followlinks=True):
            for f in files:
                if any(f.lower().endswith(ext) for ext in ['flv', 'mp4']):
                    vidlist.append((base, f))

        return vidlist

    def OnDoubleClickedRow(self, idx):
        idx = idx.row()
        path = self.model.item(idx, 2).text()
        name = self.model.item(idx, 0).text()
        vid = os.path.join(path, name)

        subprocess.Popen(vid, shell=True)

    def OnSearchKeyChanged(self):
        key = self.search_key.currentText()
        self.searchModel.setStringList(list(self.searchString[key]))
        self.completer.setModel(self.searchModel)
        self.search_line.clear()

    def OnSearchBtnClicked(self):
        text = self.search_line.text()
        key = self.search_key.currentIndex()

        self.proxy.setFilterKeyColumn(key)
        self.proxy.setFilterWildcard("*{}*".format(text) if text else "")


class MyApp(QWidget):

    def __init__(self):
        super().__init__()

        self.refVidWidget = ReferenceVideoTable()

        self.initUI()

    def initUI(self):
        mainForm = QHBoxLayout()
        self.setLayout(mainForm)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignTop)
        self.right = QVBoxLayout()

        self.contents_main = QLabel("main")
        self.contents_ref = QLabel("Ref")
        self.contents_edit = QLabel("Edit")

        self.right.addWidget(self.refVidWidget)

        mainForm.addLayout(left)
        mainForm.addLayout(self.right)

        btn_main = QPushButton('main')
        btn_ref = QPushButton('ref')
        btn_edit = QPushButton('edit')
        left.addWidget(btn_main)
        left.addWidget(btn_ref)
        left.addWidget(btn_edit)

        self.setWindowTitle('My First Application')
        self.move(300, 300)
        self.resize(1300, 500)

        # event Listener
        btn_main.clicked.connect(self.onMainBtnClick)
        btn_ref.clicked.connect(self.onRefBtnClick)
        btn_edit.clicked.connect(self.onEditBtnClick)

    def onMainBtnClick(self):
        sender = self.sender()
        self.right.removeWidget(self.contents_edit)
        self.right.removeWidget(self.contents_ref)
        self.right.addWidget(self.contents_main)
        QMessageBox.about(self, "message", "{} clicked".format(sender.text()))

    def onRefBtnClick(self):
        sender = self.sender()
        self.right.removeWidget(self.contents_edit)
        self.right.removeWidget(self.contents_main)
        self.right.addWidget(self.contents_ref)
        QMessageBox.about(self, "message", "{} clicked".format(sender.text()))

    def onEditBtnClick(self):
        sender = self.sender()
        self.right.removeWidget(self.refVidWidget)
        self.right.removeWidget(self.contents_main)
        self.right.removeWidget(self.contents_ref)
        self.right.addWidget(self.contents_edit)
        QMessageBox.about(self, "message", "{} clicked".format(sender.text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
