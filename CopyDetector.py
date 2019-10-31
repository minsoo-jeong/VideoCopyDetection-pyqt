from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
import sys
import shutil
import cv2
import subprocess
from VideoCopyDetector.Detector import Detector
from VideoEditor import FramesExtractor
from utils import *
from config import *


class VideoUploader(QWidget):
    def __init__(self):
        super().__init__()
        self.video = None

        self.tmp_query_dir = TMP_QUERY_DIR

        self.videoExtension = ['.mp4', '.avi', '.flv']
        self.frameExtractor = FramesExtractor()
        self.frameExtractor.finished.connect(self.FinishExtractFrames)

        self.subtitle = QLabel("1. Upload Video")

        self.uploadPathLineEdit = QLineEdit()
        self.uploadBtn = QPushButton()

        self.keyFrame = QLabel()
        self.keyFrame.setAlignment(Qt.AlignCenter)
        paintWidgetBackGround(self.keyFrame, COLOR_CONTENT)

        self.meta = {}
        self.videoMeta = QLabel()
        self.videoMeta.setFont(BOLD_FONT)
        self.videoMeta.setAlignment(Qt.AlignTop)


        self.parent=None

        self.InitUI()

    def InitUI(self):
        main = QGroupBox()
        mainForm = QVBoxLayout()
        mainForm.setAlignment(Qt.AlignTop)
        main.setLayout(mainForm)

        self.subtitle.setFont(BOLD_FONT)
        mainForm.addWidget(self.subtitle)

        uploadInput = QHBoxLayout()
        self.uploadPathLineEdit.setEnabled(False)
        uploadInput.addWidget(self.uploadPathLineEdit)
        self.uploadBtn.setIcon(QIcon(QPixmap("./resource/icon/icons8-upload-48.png")))
        self.uploadBtn.clicked.connect(self.OnUploadBtnClicked)
        uploadInput.addWidget(self.uploadBtn)
        mainForm.addLayout(uploadInput)

        uploadInfo = QHBoxLayout()
        self.keyFrame.setMaximumSize(300, 200)
        uploadInfo.addWidget(self.keyFrame)
        uploadInfo.addWidget(self.videoMeta)

        mainForm.addLayout(uploadInfo)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main)

    def OnUploadBtnClicked(self):
        fDialog = QFileDialog(self)
        path, _ = fDialog.getOpenFileName(self)
        path = os.path.join(path)
        print('[Upload Video] {}'.format(path))
        if os.path.splitext(path)[1] in self.videoExtension:
            self.UploadVideo(path)
        else:
            dialog = QMessageBox.about(self, "Error: Invalid File", "Only video files are accepted")
            dialog.exec_()

    def UploadVideo(self, path):
        self.parent.detectBtn.setEnabled(False)
        self.parent.setAcceptDrops(False)
        self.parent.optionSelector(False)
        self.video = path

        if os.path.exists(self.tmp_query_dir):
            shutil.rmtree(self.tmp_query_dir)
        os.makedirs(self.tmp_query_dir)

        w, h, fps, count, infoText = self.parse_video(self.video)
        self.meta.update({'width': w, 'height': h, 'fps': fps, 'count': count})
        self.videoMeta.setText(infoText)
        self.uploadPathLineEdit.setText(self.video)
        self.frameExtractor.Initialize(self.video, self.tmp_query_dir, QProgressBar(), count)
        self.frameExtractor.start()

    def parse_video(self, video_path):
        video = cv2.VideoCapture(video_path)
        w = video.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = video.get(cv2.CAP_PROP_FPS)
        count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        video.release()
        infoText = 'Size: ({},{})\n'.format(int(w), int(h))
        infoText += 'FPS: {:.2f}\n'.format(fps)
        infoText += 'nFrames: {}\n'.format(int(count))
        infoText += 'Duration: {:2f} sec\n'.format((count / fps))
        return w, h, fps, count, infoText

    def FinishExtractFrames(self):
        self.frameExtractor.stop()
        print('[Extract Frame Finish]')

        l = os.listdir(self.tmp_query_dir)
        self.keyFrame.setPixmap(QPixmap(os.path.join(self.tmp_query_dir, l[int(len(l)/2)])).scaled(300, 200, Qt.KeepAspectRatio))


        self.parent.setAcceptDrops(True)
        self.uploadBtn.setEnabled(True)
        self.parent.optionSelector.setEnabled(True)
        self.parent.detectBtn.setEnabled(True)


class OptionSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.subtitle = QLabel("2. Select Search Option")

        self.querySegmentRadioBtn_all = QRadioButton('All')
        self.querySegmentRadioBtn_partial = QRadioButton('Partial')

        self.querySegment_partial_combo = QComboBox()
        self.querySegment_partial_combo_format = [{"name": "TimeStamp", "format": "00:00:00;"},
                                                  {"name": "FrameNumber", "format": "00000;"}]
        self.partial_start = QLineEdit()
        self.partial_end = QLineEdit()

        self.smplRateLineEdit = QLineEdit()
        self.scoreThrLineEdit = QLineEdit()
        self.tempWndLineEdit = QLineEdit()
        self.topKLineEdit = QLineEdit()
        self.minPathLineEdit = QLineEdit()
        self.minMatchLineEdit = QLineEdit()

        self.InitUI()
        self.setEnabled(False)

    def InitUI(self):
        main = QGroupBox()

        mainForm = QVBoxLayout()
        mainForm.setAlignment(Qt.AlignTop)
        main.setLayout(mainForm)

        self.subtitle.setFont(BOLD_FONT)
        mainForm.addWidget(self.subtitle)

        querySegment = QFrame()
        querySegment_layout = QGridLayout()
        querySegment_layout.setAlignment(Qt.AlignLeft)
        querySegment_layout.setContentsMargins(0, 0, 0, 0)

        querySegment.setLayout(querySegment_layout)
        querySegment_label = QLabel("Query Segment")
        querySegment_label.setFont(BOLD_FONT)
        querySegment_layout.addWidget(querySegment_label, 0, 0)
        querySegment_layout.addWidget(self.querySegmentRadioBtn_all, 1, 0)
        querySegment_layout.addWidget(self.querySegmentRadioBtn_partial, 2, 0)
        self.querySegmentRadioBtn_all.toggled.connect(self.OnQuerySegmentAll_toggle)
        self.querySegmentRadioBtn_partial.toggled.connect(self.OnQuerySegmentPartial_toggle)
        self.querySegmentRadioBtn_all.toggle()
        [self.querySegment_partial_combo.addItem(f['name'], f['format']) for f in
         self.querySegment_partial_combo_format]
        querySegment_layout.addWidget(QLabel('start'), 3, 1)
        querySegment_layout.addWidget(QLabel('end'), 3, 2)
        querySegment_layout.addWidget(self.querySegment_partial_combo, 4, 0)
        querySegment_layout.addWidget(self.partial_start, 4, 1)
        querySegment_layout.addWidget(self.partial_end, 4, 2)

        self.querySegment_partial_combo.currentIndexChanged.connect(self.OnQuerySegmentPartialComboBoxChanged)

        parameters = QFrame()
        parameters_layout = QGridLayout()
        parameters_layout.setAlignment(Qt.AlignLeft)
        parameters.setLayout(parameters_layout)

        smplRate_label = QLabel("Sampling Frames Per Second (1-30)")
        smplRate_label.setFont(BOLD_FONT)
        parameters_layout.addWidget(smplRate_label, 0, 0)
        parameters_layout.addWidget(self.smplRateLineEdit, 0, 1)
        self.smplRateLineEdit.setText('1')

        label = QLabel("Temporal Network - Score Threshold (0.0-1.0)")
        label.setFont(BOLD_FONT)
        parameters_layout.addWidget(label, 1, 0)
        parameters_layout.addWidget(self.scoreThrLineEdit, 1, 1)
        self.scoreThrLineEdit.setText("0.95")

        label = QLabel("Temporal Network - TopK (10-100)")
        label.setFont(BOLD_FONT)
        parameters_layout.addWidget(label, 2, 0)
        parameters_layout.addWidget(self.topKLineEdit, 2, 1)
        self.topKLineEdit.setText('50')

        label = QLabel("Temporal Network - Temporal Window Size")
        label.setFont(BOLD_FONT)
        parameters_layout.addWidget(label, 3, 0)
        parameters_layout.addWidget(self.tempWndLineEdit, 3, 1)
        self.tempWndLineEdit.setText('1')

        label = QLabel("Temporal Network - Minimum Path")
        label.setFont(BOLD_FONT)
        parameters_layout.addWidget(label, 4, 0)
        parameters_layout.addWidget(self.minPathLineEdit, 4, 1)
        self.minPathLineEdit.setText('2')

        label = QLabel("Temporal Network - Minimum Match")
        label.setFont(BOLD_FONT)
        parameters_layout.addWidget(label, 5, 0)
        parameters_layout.addWidget(self.minMatchLineEdit, 5, 1)
        self.minMatchLineEdit.setText('2')

        mainForm.addWidget(querySegment)
        mainForm.addWidget(parameters)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main)

    def OnQuerySegmentAll_toggle(self, enable):
        if enable:
            self.querySegment_partial_combo.setEnabled(False)
            self.partial_start.setEnabled(False)
            self.partial_end.setEnabled(False)

    def OnQuerySegmentPartial_toggle(self, enable):
        if enable:
            self.querySegment_partial_combo.setEnabled(True)
            self.partial_start.setEnabled(True)
            self.partial_end.setEnabled(True)
            self.OnQuerySegmentPartialComboBoxChanged(0)

    def OnQuerySegmentPartialComboBoxChanged(self, idx):
        self.partial_start.clear()
        self.partial_end.clear()
        self.partial_start.setInputMask(self.querySegment_partial_combo.itemData(idx, Qt.UserRole))
        self.partial_end.setInputMask(self.querySegment_partial_combo.itemData(idx, Qt.UserRole))

        if self.querySegment_partial_combo.currentIndex() == 0:
            self.partial_start.setText('00:00:00')
            self.partial_end.setText('00:00:00')
        else:
            self.partial_start.setText('00000')
            self.partial_end.setText('00000')

        self.partial_start.setCursorPosition(0)
        self.partial_start.setFocus()


class ResultViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.queryVideo=None
        self.subtitle=QLabel("3. Result")
        self.resultTable = QTableWidget(0, 7)
        self.model = QStandardItemModel(self)

        self.InitUI()

    def InitUI(self):
        main = QGroupBox()
        mainForm = QVBoxLayout()
        mainForm.setAlignment(Qt.AlignTop)
        mainForm.setContentsMargins(10, 10, 10, 10)
        main.setLayout(mainForm)

        self.subtitle.setFont(BOLD_FONT)
        mainForm.addWidget(self.subtitle)

        self.InitTable()

        mainForm.addWidget(self.resultTable)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main)
        self.resultTable.doubleClicked.connect(self.OnDoubleClickedRow)

    def InitTable(self):
        header = self.resultTable.horizontalHeader()
        self.resultTable.setHorizontalHeaderLabels(
            ['q Start', 'q End', 'Ref Title', 'Ref name', 'ref start', 'ref end', 'score'])
        self.resultTable.resizeRowsToContents()
        self.resultTable.setSortingEnabled(False)
        self.resultTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.resultTable.setSelectionMode(QTableWidget.SingleSelection)
        self.resultTable.setEditTriggers(QTableWidget.NoEditTriggers)

    def addRow(self, data):
        rowPosition = self.resultTable.rowCount()
        self.resultTable.insertRow(rowPosition)
        qstart, qend, refTitle, refName, refstart, refend, score = data
        qstart = QTableWidgetItem(str(round(qstart,2)))
        qend = QTableWidgetItem(str(round(qend, 2)))
        refName = QTableWidgetItem(refName)
        refTitle = QTableWidgetItem(refTitle)
        refstart = QTableWidgetItem(str(round(refstart, 2)))
        refend = QTableWidgetItem(str(round(refend, 2)))
        score = QTableWidgetItem(str(round(score, 2)))
        color = COLOR_TABLE_1 if rowPosition % 2 == 0 else COLOR_TABLE_2

        def foo(x,c):
            x.setTextAlignment(Qt.AlignCenter)
            x.setBackground(QBrush(c))
            return x

        rowItems = list(map(lambda x: foo(x,color), [qstart, qend, refTitle, refName, refstart, refend, score]))

        [self.resultTable.setItem(rowPosition, n, i) for n, i in enumerate(rowItems)]

    def setTable(self,results):
        self.resultTable.clear()
        self.InitTable()
        self.resultTable.setRowCount(0)
        for r in results:
            self.addRow((r['query'].start, r['query'].end, r['ref_title'], r['ref_name'], r['ref'].start,
                                      r['ref'].end, r['score']))


    def OnDoubleClickedRow(self,idx):
        idx = idx.row()
        q=self.queryVideo
        rtitle=self.resultTable.item(idx, 2).text()
        rname = self.resultTable.item(idx, 3).text()
        r=os.path.join(REFERENCE_VIDEO_DIR,'core_dataset',rtitle,rname)

        qstart=float(self.resultTable.item(idx, 0).text())
        rstart = float(self.resultTable.item(idx, 4).text())
        def foo(t):
            h,t=divmod(t,3600)
            m,t=divmod(t,60)
            s=int(t)
            ms=(t-s)*100
            return '{}:{}:{}.{}'.format(int(h),int(m),int(s),int(ms))
        qstart=foo(qstart)
        rstart=foo(rstart)

        cmd1=['C:/Program Files (x86)/Daum/PotPlayer/PotPlayer.exe',q,'/seek={}'.format(qstart)]
        cmd2 = ['C:/Program Files (x86)/Daum/PotPlayer/PotPlayer.exe', r, '/seek={}'.format(rstart)]
        print('[DoubleClickRow] Play: {} {}'.format(cmd1, cmd2))
        p1=subprocess.Popen(cmd1, shell=True)
        p2=subprocess.Popen(cmd2, shell=True)

class CopyDetector(QWidget):
    def __init__(self):
        super().__init__()
        self.queryDir = QUERY_DIR
        self.setAcceptDrops(True)
        self.videoExtension = ['.mp4', '.avi', '.flv']
        self.videoUploader = VideoUploader()
        self.detectBtn = QPushButton()
        self.optionSelector = OptionSelector()

        self.resultViewer = ResultViewer()


        self.referenceVideo = None
        self.detector = Detector(cuda=True)

        self.InitUI()

        self.videoUploader.parent=self

    def InitUI(self):
        mainForm = QHBoxLayout()
        mainForm.setContentsMargins(10, 10, 10, 10)
        mainForm.setAlignment(Qt.AlignTop)
        self.setLayout(mainForm)

        left = QGroupBox()
        left_layout = QVBoxLayout()
        left.setLayout(left_layout)
        left.setAlignment(Qt.AlignTop)
        left.setMaximumWidth(500)

        left_layout.addWidget(self.videoUploader)
        left_layout.addWidget(self.optionSelector)
        mainForm.addWidget(left)

        self.detectBtn.setIcon(QIcon('./resource/icon/icons8-double-right-96.png'))
        self.detectBtn.setEnabled(False)
        self.detectBtn.clicked.connect(self.Detect)

        mainForm.addWidget(self.detectBtn)

        right = self.resultViewer
        mainForm.addWidget(right)

    def parseTimer(self, len_frames, videoFps):
        start = 0
        end = len_frames - 1

        if self.optionSelector.querySegmentRadioBtn_partial.isChecked():
            start = self.optionSelector.partial_start.text()
            end = self.optionSelector.partial_end.text()
            if self.optionSelector.querySegment_partial_combo.currentIndex() == 0:
                start = int(sum([i * (60 ** (2 - n)) for n, i in
                                 enumerate(list(map(lambda x: int('0' + x), start.split(":"))))]) * videoFps)
                end = int(sum([i * (60 ** (2 - n)) for n, i in
                               enumerate(list(map(lambda x: int('0' + x), end.split(":"))))]) * videoFps)
            else:
                start = 0 if not len(start) else int(start)
                end = 0 if not len(end) else int(end)

        # valid start - end
        (start, end) = (end, start) if start > end else (start, end)
        start = max(0, start)
        end = min(len_frames - 1, end)
        print('[Parse Frame Index] {} - {}'.format(start, end))

        return start, end

    def Detect(self):
        self.setEnabled(False)
        self.resultViewer.queryVideo = self.videoUploader.video
        frames = sorted(os.listdir(TMP_QUERY_DIR))
        videoFps = self.videoUploader.meta['fps']
        smplFps = int(self.optionSelector.smplRateLineEdit.text())
        interval = videoFps / smplFps if videoFps >= smplFps else 1
        start, end = self.parseTimer(len(frames), videoFps)

        # query Frame Sampling
        if os.path.exists(self.queryDir):
            shutil.rmtree(self.queryDir)
        os.makedirs(self.queryDir)

        frame_indices = [int(i) for i in np.arange(start + (interval / 2), end + 1, interval)]
        [shutil.copy(os.path.join(TMP_QUERY_DIR, frames[i]), os.path.join(self.queryDir, frames[i])) for i in
         frame_indices]

        TOPK = int(self.optionSelector.topKLineEdit.text())
        TEMPWND = int(self.optionSelector.tempWndLineEdit.text())
        SCORETHR = float(self.optionSelector.scoreThrLineEdit.text())
        MINPATH = int(self.optionSelector.minPathLineEdit.text())
        MINMATCH = int(self.optionSelector.minMatchLineEdit.text())

        print('[Detect Partial Copy] SCORE_THR: {}, TOP_K: {} TEMP_WND: {}, MIN_PATH: {}, MIN_MATCH: {}'
              .format(SCORETHR, TOPK, TEMPWND, MINPATH, MINMATCH))

        # Load Pre extracted Feature
        result = self.detector.detect(QUERY_DIR, start / videoFps, smplFps, self.referenceVideo, TOPK, SCORETHR,
                                      TEMPWND,
                                      MINPATH, MINMATCH)

        print(result)
        self.resultViewer.setTable(result)

        self.setEnabled(True)


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
            path = os.path.join(str(urls[0].path())[1:])
            print('[Drop Video] {}'.format(path))
            if os.path.splitext(path)[1] in self.videoExtension:
                self.videoUploader.UploadVideo(path)
            else:
                dialog = QMessageBox.about(self, "Error: Invalid File", "Only video files are accepted")
                dialog.exec_()


if __name__ == '__main__':
    from App import MyApp

    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
