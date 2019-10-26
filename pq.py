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

COLOR_WORKLIST = QColor(149, 117, 205)
COLOR_WORKLIST_over = QColor(209, 196, 233)
COLOR_CONTENT = QColor(250, 250, 250)
COLOR_CONTENT_2 = QColor(200, 200, 200)
COLOR_TABLE_1 = QColor(245, 245, 245)
COLOR_TABLE_2 = QColor(250, 250, 250)


def paintWidgetBackGround(widget, color):
    widget.setAutoFillBackground(True)
    p = widget.palette()
    p.setColor(widget.backgroundRole(), color)
    widget.setPalette(p)


class ReferenceVideoTable(QWidget):
    def __init__(self, *args, **kwargs):
        super(ReferenceVideoTable, self).__init__(*args, **kwargs)
        self.root = os.path.abspath('./data')
        '''
        make symbolic link for Windows
        mklink /D "core_dataset_video" "D:\copydetection-app-data\core_dataset\videos\core_dataset\videos"
        '''

        self.ref_vid = self.scan_ref_vid()
        self.tableHeader = ["Filename", "Title", "Path", "FPS", "Duration", "Frames"]

        # filter table
        self.searchString = {"Filename": set(), "Title": set(), "Path": set()}
        self.videoExtension = ['.mp4', '.avi', '.flv']

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
        self.videoTable.setSortingEnabled(True)

        self.model.setHorizontalHeaderLabels(self.tableHeader)

        header = self.videoTable.horizontalHeader()

        self.videoTable.setShowGrid(False)

        self.videoTable.setSelectionBehavior(QTableView.SelectRows)
        self.videoTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.videoTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for n, (path, name) in enumerate(self.ref_vid):
            self.addRow(n, (name, os.path.basename(path), path, "0", "0", "0"))

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
        print('[Scan videos] root {} '.format(self.root))
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
        print('[DoubleClickRow] Play: {} '.format(vid))

        subprocess.Popen(vid, shell=True)

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


class FramesExtractor(QThread):
    finished = pyqtSignal()
    read = pyqtSignal(int, str)

    def __init__(self, *args, **kwargs):
        super(FramesExtractor, self).__init__(*args, **kwargs)
        self.video = None
        self.outdir = None

    def Initialize(self, video_path, output_dir, prgs, count):
        self.video = video_path
        self.outdir = output_dir
        self.prgs = prgs
        self.count = count
        self.prgs.setMaximum(count)
        # self.vid = cv2.VideoCapture(self.video)

    def run(self):
        cmd = 'ffmpeg -i {} -f image2 {}'.format(self.video, os.path.join(self.outdir, '%6d.jpg').replace('\\', '/'))
        print('[Extract Frames] {}'.format(cmd))
        p = subprocess.Popen(args=cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, )
        '''
        while p.poll() is None:
            print(len(os.listdir(self.outdir)))
            self.prgs.setValue(len(os.listdir(self.outdir)))
            time.sleep(0.5)
        '''
        out, err = p.communicate()
        if p.returncode == 0:
            self.prgs.setValue(self.count)
        self.finished.emit()

        '''
        while self.vid.isOpened():
            ret, f = self.vid.read()
            if not ret:
                break
            t = os.path.join(self.outdir, '{}.jpg'.format(str(self.cnt).zfill(6)))
            cv2.imwrite(t, f)
            self.read.emit(self.cnt, t)
            self.prgs.setValue(self.cnt)
            self.cnt += 1
        self.prgs.setMaximum(self.cnt-1)
        self.finished.emit()
        '''

    def stop(self):
        self.wait()


class VideoEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.videoExtension = ['.mp4', '.avi', '.flv']
        self.tmp_dir = os.path.abspath('./tmp')
        self.tmp_frame_dir = os.path.join(self.tmp_dir, 'frames')
        self.frameExtractor = FramesExtractor()

        self.initUI()
        paintWidgetBackGround(self, COLOR_CONTENT)

        self.video = None
        self.frames = None

    def initUI(self):
        mainForm = QHBoxLayout()
        mainForm.setContentsMargins(10, 10, 10, 10)

        '''
        frame Selector
        '''
        frameSelector = QGroupBox()
        frameSelector_layout = QVBoxLayout()
        frameSelector.setLayout(frameSelector_layout)

        # subtitle
        frameSelector_subtitle = QLabel("1. Select Frames")
        font_bold = QFont()
        font_bold.setBold(True)
        frameSelector_subtitle.setFont(font_bold)
        frameSelector_subtitle.setAlignment(Qt.AlignTop)
        frameSelector_layout.addWidget(frameSelector_subtitle)

        # 1. video upload (+ drag n drop)
        self.upload_videoInfo = QLabel("info")
        self.prgs = QProgressBar()
        self.prgs.setValue(0)

        upload_widget = QGroupBox()
        upload_widget_layout = QVBoxLayout()
        upload_widget.setLayout(upload_widget_layout)

        upload_file = QHBoxLayout()
        self.upload_btn = QPushButton()
        self.upload_btn.setIcon(QIcon(QPixmap("./resource/icon/icons8-upload-48.png")))

        self.upload_lineEdit = QLineEdit()
        self.upload_lineEdit.setEnabled(False)

        upload_file.addWidget(self.upload_lineEdit)
        upload_file.addWidget(self.upload_btn)

        upload_widget_layout.addWidget(self.prgs)
        upload_widget_layout.addLayout(upload_file)
        upload_widget_layout.addWidget(self.upload_videoInfo)

        frameSelector_layout.addWidget(upload_widget)

        # 2. frame list (filter + table)
        frameTable_widget = QGroupBox()
        frameTable_widget_layout = QVBoxLayout()
        frameTable_widget.setLayout(frameTable_widget_layout)

        # filter Combobox + lineEdit
        frameTable_filter_layout = QGridLayout()
        self.frameTable_filter_combobox = QComboBox()
        frameTable_filter_combobox_format = [{"name": "FrameNumber", "format": "00000;"},
                                             {"name": "TimeStamp", "format": "00:00:00;"}]
        [self.frameTable_filter_combobox.addItem(f['name'], f['format']) for f in frameTable_filter_combobox_format]

        start = QLabel('START')
        end = QLabel('END')
        frameTable_filter_layout.addWidget(start, 0, 1)
        frameTable_filter_layout.addWidget(end, 0, 2)
        frameTable_filter_layout.addWidget(self.frameTable_filter_combobox, 1, 0)

        self.frameTable_filter_lineEdit_start = QLineEdit()
        self.frameTable_filter_lineEdit_end = QLineEdit()
        self.frameTable_filter_lineEdit_start.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.frameTable_filter_lineEdit_end.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.frameTable_filter_apply_btn = QPushButton()
        self.frameTable_filter_apply_btn.setIcon(QIcon('./resource/icon/icons8-sync-48.png'))

        frameTable_filter_layout.addWidget(self.frameTable_filter_lineEdit_start, 1, 1)
        frameTable_filter_layout.addWidget(self.frameTable_filter_lineEdit_end, 1, 2)
        frameTable_filter_layout.addWidget(self.frameTable_filter_apply_btn, 1, 3)
        frameTable_widget_layout.addLayout(frameTable_filter_layout)

        self.frameTable_filter_lineEdit_start.setEnabled(False)
        self.frameTable_filter_lineEdit_end.setEnabled(False)
        self.frameTable_filter_apply_btn.setEnabled(False)
        self.OnFrameTableFiltercomboBoxChanged(0)

        self.frameTable_filter_apply_btn.clicked.connect(self.OnFrameTableFilterApplyBtnClicked)

        self.selected_filter_start = QLabel("0")
        self.selected_filter_end = QLabel("0")

        frameTable_filter_layout.addWidget(self.selected_filter_start, 2, 1)
        frameTable_filter_layout.addWidget(self.selected_filter_end, 2, 2)

        # table
        self.frameTable = QTableView()
        self.model = QStandardItemModel()
        self.frameTable.setModel(self.model)
        self.frameTable.setSortingEnabled(False)
        self.frameTable.setShowGrid(False)
        self.model.setColumnCount(4)
        self.model.setHorizontalHeaderLabels(['Thumbnail', 'start', 'end', 'path'])

        self.frameTable.setSelectionBehavior(QTableView.SelectRows)
        self.frameTable.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.frameTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.frameTable_selectioModel = self.frameTable.selectionModel()

        header = self.frameTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        frameTable_widget_layout.addWidget(self.frameTable)

        frameSelector_layout.addWidget(frameTable_widget)
        mainForm.addWidget(frameSelector)

        self.toQueryEditorBtn = QPushButton()
        self.toQueryEditorBtn.setIcon(QIcon('./resource/icon/icons8-double-right-96.png'))
        self.toQueryEditorBtn.setEnabled(False)
        mainForm.addWidget(self.toQueryEditorBtn)

        '''
        Edit Query
        '''
        queryEditor = QGroupBox()
        queryEditor_layout = QVBoxLayout()
        queryEditor.setLayout(queryEditor_layout)
        # subtitle
        queryEditor_subtitle = QLabel("2. Edit Query")
        queryEditor_subtitle.setFont(font_bold)
        queryEditor_subtitle.setAlignment(Qt.AlignTop)
        queryEditor_layout.addWidget(queryEditor_subtitle)

        im = QLabel()
        im.setPixmap(QPixmap('./resource/icon/dragndrop.png'))
        im.setFixedWidth(500)
        im.setFixedHeight(500)
        im.setAlignment(Qt.AlignHCenter)
        queryEditor_layout.addWidget(im)

        tools = QLabel('tool')

        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignVCenter)

        torightbtn = QPushButton('>>')
        torightbtn.setEnabled(False)

        mainForm.addWidget(queryEditor)

        mainForm.addLayout(center_layout)

        self.setLayout(mainForm)
        self.upload_btn.clicked.connect(self.OnUploadBtnClicked)

        # self.frameExtractor.read.connect(self.addRow)
        self.frameExtractor.finished.connect(self.FinishExtractFrames)
        self.frameTable_selectioModel.selectionChanged.connect(self.selectFrames)
        self.frameTable_filter_combobox.currentIndexChanged.connect(self.OnFrameTableFiltercomboBoxChanged)

        self.toQueryEditorBtn.clicked.connect(self.OnToQueryEditorBtnClicked)

        # self.frameList.clicked.connect(self.selectFrames)
        # self.frameList.drag.connect(self.selectFrames)

    def OnToQueryEditorBtnClicked(self):
        start = int(self.selected_filter_start.text())
        end = int(self.selected_filter_end.text())
        frame_idx = int((end - start + 1) / 2) + start
        l = os.listdir(self.tmp_frame_dir)
        print(frame_idx, l[frame_idx])

    def OnFrameTableFilterApplyBtnClicked(self):
        self.frameTable.reset()

        start = self.frameTable_filter_lineEdit_start.text()
        end = self.frameTable_filter_lineEdit_end.text()
        if self.frameTable_filter_combobox.currentIndex() == 0:
            start = 0 if not len(start) else int(start)
            end = 0 if not len(end) else int(end)
        else:
            start = int(sum([i * (60 ** (2 - n)) for n, i in
                             enumerate(list(map(lambda x: int('0' + x), start.split(":"))))]) * self.fps)
            end = int(sum([i * (60 ** (2 - n)) for n, i in
                           enumerate(list(map(lambda x: int('0' + x), end.split(":"))))]) * self.fps)
        print('[Filter Apply] {} - {}'.format(start, end))
        self.frameTable.setSelectionMode(QAbstractItemView.MultiSelection)
        for i in range(self.model.rowCount()):
            if start <= int(self.model.item(i, 1).text()) <= end or start <= int(self.model.item(i, 2).text()) <= end:
                self.frameTable.selectRow(i)

        self.frameTable.setSelectionMode(QAbstractItemView.ContiguousSelection)

        self.selected_filter_start.setText(str(start))
        self.selected_filter_end.setText(str(end))

    def OnFrameTableFiltercomboBoxChanged(self, idx):
        self.frameTable_filter_lineEdit_start.clear()
        self.frameTable_filter_lineEdit_end.clear()
        self.frameTable_filter_lineEdit_start.setInputMask(self.frameTable_filter_combobox.itemData(idx, Qt.UserRole))
        self.frameTable_filter_lineEdit_end.setInputMask(self.frameTable_filter_combobox.itemData(idx, Qt.UserRole))

        if self.frameTable_filter_combobox.currentIndex() == 0:
            self.frameTable_filter_lineEdit_start.setText('00000')
            self.frameTable_filter_lineEdit_end.setText('00000')
        else:
            self.frameTable_filter_lineEdit_start.setText('00:00:00')
            self.frameTable_filter_lineEdit_end.setText('00:00:00')

        self.frameTable_filter_lineEdit_start.setCursorPosition(0)
        self.frameTable_filter_lineEdit_start.setFocus()

    def selectFrames(self):

        s = [(self.model.item(i.row(), 1).text(), self.model.item(i.row(), 2).text())
             for i in self.frameTable_selectioModel.selectedRows()]

        start = min(s, key=lambda x: int(x[0]))[0]
        end = max(s, key=lambda x: int(x[1]))[1]
        print('[Select Frames] start: {}, end: {}'.format(start, end, s))
        self.selected_filter_start.setText(start)
        self.selected_filter_end.setText(end)

        self.toQueryEditorBtn.setEnabled(True)

    def dragEnterEvent(self, e):
        e.accept()
        data = e.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file' and os.path.splitext(urls[0].fileName())[0] in self.videoExtension:
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        data = e.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file' and os.path.splitext(urls[0].fileName())[0] in self.videoExtension:
            e.acceptProposedAction()

    def dropEvent(self, e):
        data = e.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            self.video = os.path.join(str(urls[0].path())[1:])
            print('[Drop Video] {}'.format(self.video))
            if os.path.splitext(self.video)[1] in self.videoExtension:
                self.split_frame()
            else:
                dialog = QMessageBox.about(self, "Error: Invalid File", "Only video files are accepted")
                dialog.exec_()

    def OnUploadBtnClicked(self):
        fDialog = QFileDialog(self)
        path, _ = fDialog.getOpenFileName(self)
        self.video = os.path.join(path)
        print('[Upload Video] {}'.format(self.video))
        if os.path.splitext(self.video)[1] in self.videoExtension:
            self.split_frame()
        else:
            dialog = QMessageBox.about(self, "Error: Invalid File", "Only video files are accepted")
            dialog.exec_()

    def split_frame(self):
        # 0. Enable upload n Drag drop
        self.upload_btn.setEnabled(False)
        self.setAcceptDrops(False)

        # 1. extract video meta & show
        if os.path.exists(self.tmp_frame_dir):
            shutil.rmtree(self.tmp_frame_dir)
        os.makedirs(self.tmp_frame_dir)

        # 1. extract video meta & show
        width, height, fps, count = self.parse_video(self.video)
        self.intv = int(fps / 2)
        self.fps = fps
        infoText = 'Size: ({},{})\n'.format(int(width), int(height))
        infoText += 'FPS: {}\n'.format(fps)
        infoText += 'nFrames: {}\n'.format(int(count))
        infoText += 'Duration: {}\n'.format(count / fps)
        print('[Video MetaData] {}'.format(infoText.replace('\n', '\t')))
        self.upload_videoInfo.setText(infoText)
        self.upload_lineEdit.setText(self.video)
        # 2. extract video frames--> thread & show progressbar & add Frame List
        self.deleteAllRow()
        self.frameExtractor.Initialize(self.video, self.tmp_frame_dir, self.prgs, count)
        self.frameExtractor.start()

    def FinishExtractFrames(self):
        self.frameExtractor.stop()
        print('[Extract Frame Finish]')
        l = os.listdir(self.tmp_frame_dir)
        for n, i in enumerate(l):
            self.addRow(n, os.path.join(self.tmp_frame_dir, i))

        self.frameTable_filter_lineEdit_start.setEnabled(True)
        self.frameTable_filter_lineEdit_end.setEnabled(True)
        self.frameTable_filter_apply_btn.setEnabled(True)

        self.upload_btn.setEnabled(True)
        self.setAcceptDrops(True)

    def deleteAllRow(self):
        self.model.setRowCount(0)

    def addRow(self, idx, path):
        # 3. fill Frame list ( thumbnail, frmae idx, timestamp
        if idx % self.intv == 0:
            qpix = QPixmap(path).scaled(100, 100, Qt.KeepAspectRatio)
            thumb = QStandardItem()
            thumb.setData(QVariant(qpix), Qt.DecorationRole)
            path = QStandardItem(path)
            start = QStandardItem(str(idx))
            end = QStandardItem(str(idx + self.intv - 1))
            rowItems = [thumb, start, end, path]

            color = COLOR_TABLE_1 if self.model.rowCount() % 2 == 0 else COLOR_TABLE_2
            [i.setBackground(QBrush(color)) for i in rowItems]
            self.model.appendRow(rowItems)

    def parse_video(self, video_path):
        video = cv2.VideoCapture(video_path)
        w = video.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = video.get(cv2.CAP_PROP_FPS)
        count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        video.release()
        return w, h, fps, count


class MPanel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(MPanel, self).__init__(*args, **kwargs)
        self.setText(args[0])
        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(70)
        # self.setFixedWidth(100)
        self.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name))

    def enterEvent(self, e):
        self.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST_over.name()))

    def leaveEvent(self, e):
        self.setStyleSheet('color: Black; background-color:{};'.format(COLOR_WORKLIST.name()))

    def mouseReleaseEvent(self, e):
        self.clicked.emit()


class MyApp(QWidget):

    def __init__(self, *args, **kwargs):
        super(MyApp, self).__init__(*args, **kwargs)

        self.tabs = QTabWidget()

        self.tabs.addTab(QFrame(), 'main')
        self.tabs.addTab(ReferenceVideoTable(), 'ref')
        self.tabs.addTab(VideoEditor(), 'edit')
        self.tabs.tabBar().hide()
        self.tabs.setContentsMargins(0, 0, 0, 0)
        self.tabs.setCurrentIndex(2)

        # self.tabs.setStyleSheet('border:1px')

        self.initUI()

    def initUI(self):
        self.setWindowTitle('My First Application')
        self.move(200, 200)
        self.resize(1200, 600)
        mainForm = QHBoxLayout()
        mainForm.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainForm)

        left = QGroupBox()
        left_layout = QVBoxLayout()
        left.setLayout(left_layout)

        left_layout.setAlignment(Qt.AlignTop)
        left_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        left_layout.setContentsMargins(0, 0, 0, 0)

        btn_main = MPanel('main')
        btn_ref = MPanel('Ref')
        btn_edit = MPanel('edit')

        left_layout.addWidget(btn_main)
        left_layout.addWidget(btn_ref)
        left_layout.addWidget(btn_edit)
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
        btn_main.clicked.connect(self.onMainBtnClick)
        btn_ref.clicked.connect(self.onRefBtnClick)
        btn_edit.clicked.connect(self.onEditBtnClick)

    def onMainBtnClick(self):
        sender = self.sender()
        self.tabs.setCurrentIndex(0)
        # QMessageBox.about(self, "message", "{} clicked".format(sender.text()))

    def onRefBtnClick(self):
        sender = self.sender()
        self.tabs.setCurrentIndex(1)
        # QMessageBox.about(self, "message", "{} clicked".format(sender.text()))

    def onEditBtnClick(self):
        sender = self.sender()
        self.tabs.setCurrentIndex(2)
        # QMessageBox.about(self, "message", "{} clicked".format(sender.text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
