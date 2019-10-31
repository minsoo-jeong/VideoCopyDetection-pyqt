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
import random
from utils import *
from config import *


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
        out, err = p.communicate()
        if p.returncode == 0:
            self.prgs.setValue(self.count)
        self.finished.emit()

    def stop(self):
        self.wait()


class PaintView(QGraphicsView):
    def __init__(self, cntr, parent):
        super().__init__(parent)
        self.cntr = cntr
        self.scene = QGraphicsScene(self)
        self.setStyleSheet("background: transparent")

        self.setScene(self.scene)

        self.items = []

        self.start = QPointF()
        self.end = QPointF()

        self.setRenderHint(QPainter.HighQualityAntialiasing)

    def moveEvent(self, e):
        rect = QRectF(self.rect())
        rect.adjust(0, 0, -2, -2)

        self.scene.setSceneRect(rect)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            # 시작점 저장
            self.start = e.pos()
            self.end = e.pos()
            print('[Click] {} {}'.format(self.start, self.end))

    def mouseMoveEvent(self, e):

        # e.buttons()는 정수형 값을 리턴, e.button()은 move시 Qt.Nobutton 리턴
        if e.buttons() & Qt.LeftButton:
            self.end = e.pos()
            '''
            # 지우개
            if self.cntr.checkbox.isChecked():
                pen = QPen(QColor(255, 255, 255), 10)
                path = QPainterPath()
                path.moveTo(self.start)
                path.lineTo(self.end)
                self.scene.addPath(path, pen)
                self.start = e.pos()
                return None
            '''

            pen = QPen(self.cntr.pencolor, self.cntr.line_combo.currentIndex())
            # 직선 그리기
            if self.cntr.paintTool == 0:

                # 장면에 그려진 이전 선을 제거
                if len(self.items) > 0:
                    self.scene.removeItem(self.items[-1])
                    del (self.items[-1])

                    # 현재 선 추가
                line = QLineF(self.start.x(), self.start.y(), self.end.x(), self.end.y())
                self.items.append(self.scene.addLine(line, pen))

            # 곡선 그리기
            if self.cntr.paintTool == 1:
                # Path 이용
                path = QPainterPath()
                path.moveTo(self.start)
                path.lineTo(self.end)
                self.scene.addPath(path, pen)

                # Line 이용
                # line = QLineF(self.start.x(), self.start.y(), self.end.x(), self.end.y())
                # self.scene.addLine(line, pen)

                # 시작점을 다시 기존 끝점으로
                self.start = e.pos()

            # 사각형 그리기
            if self.cntr.paintTool == 2:
                brush = QBrush(self.cntr.brushcolor)

                if len(self.items) > 0:
                    self.scene.removeItem(self.items[-1])
                    del (self.items[-1])

                rect = QRectF(self.start, self.end)
                self.items.append(self.scene.addRect(rect, pen, brush))

            # 원 그리기
            if self.cntr.paintTool == 3:
                brush = QBrush(self.cntr.brushcolor)

                if len(self.items) > 0:
                    self.scene.removeItem(self.items[-1])
                    del (self.items[-1])

                rect = QRectF(self.start, self.end)
                self.items.append(self.scene.addEllipse(rect, pen, brush))

            if self.cntr.paintTool == 4:
                pen = QPen()
                pen.setStyle(Qt.DashDotDotLine)
                pen.setColor(Qt.black)
                brush = QBrush(Qt.transparent)

                if len(self.items) > 0:
                    self.scene.removeItem(self.items[-1])
                    del (self.items[-1])

                rect = QRectF(self.start, self.end)
                self.items.append(self.scene.addRect(rect, pen, brush))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:

            '''
            if self.cntr.checkbox.isChecked():
                return None
            '''
            pen = QPen(self.cntr.pencolor, self.cntr.line_combo.currentIndex())

            if self.cntr.paintTool == 0:
                self.items.clear()
                line = QLineF(self.start.x(), self.start.y(), self.end.x(), self.end.y())

                self.scene.addLine(line, pen)

            if self.cntr.paintTool == 2:
                brush = QBrush(self.cntr.brushcolor)

                self.items.clear()
                rect = QRectF(self.start, self.end)
                self.scene.addRect(rect, pen, brush)

            if self.cntr.paintTool == 3:
                brush = QBrush(self.cntr.brushcolor)
                self.items.clear()
                rect = QRectF(self.start, self.end)
                self.scene.addEllipse(rect, pen, brush)

            if self.cntr.paintTool == 4:
                rect = QRectF(self.start, self.end)
                if len(self.items) > 0:
                    self.scene.removeItem(self.items[-1])
                    del (self.items[-1])

                text = QGraphicsTextItem("this is text")
                text.setFont(self.cntr.font)
                text.setPos(self.start)
                self.scene.addItem(text)


class VideoEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.videoExtension = ['.mp4', '.avi', '.flv']
        self.tmp_dir = TMP_DIR
        self.tmp_frame_dir = os.path.join(self.tmp_dir, 'frames')
        self.frameExtractor = FramesExtractor()

        self.bg_im = os.path.join(self.tmp_dir, 'bg.jpg')
        self.paint_im = os.path.join(self.tmp_dir, 'paint.png')

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

        frameSelector_subtitle.setFont(BOLD_FONT)
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

        self.frameTable.setSelectionBehavior(QTableView.SelectRows)
        self.frameTable.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.frameTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.frameTable_selectioModel = self.frameTable.selectionModel()
        self.initFrameTableSetting()

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
        queryEditor_subtitle.setFont(BOLD_FONT)
        queryEditor_subtitle.setAlignment(Qt.AlignTop)
        queryEditor_layout.addWidget(queryEditor_subtitle)

        ################################
        self.query_container = QFrame(self)
        self.query_container.setFixedWidth(500)
        self.query_container.setFixedHeight(300)
        self.query_container_layout = QVBoxLayout()
        self.query_container_layout.setContentsMargins(0, 0, 0, 0)
        self.query_container_layout.setAlignment(Qt.AlignTop)
        self.query_container.setLayout(self.query_container_layout)

        queryEditor_layout.addWidget(self.query_container)

        ########## painter (overlay)

        self.paint = PaintView(self, self.query_container)
        self.query_container_layout.addWidget(self.paint)

        self.ToBackground('./resource/icon/dragndrop.png')
        self.origin = './resource/icon/dragndrop.png'

        ########## tools
        paintgb = QGroupBox('Paint')
        paintgb_layout = QHBoxLayout()
        paintgb.setLayout(paintgb_layout)

        toolgb = QGroupBox('도구')
        toolgb_layout = QVBoxLayout()
        toolgb.setLayout(toolgb_layout)

        text = ['Line', 'Curve', 'Rectange', 'Ellipse', 'Text']
        self.tool_radiobtns = []

        for i in range(len(text)):
            self.tool_radiobtns.append(QRadioButton(text[i], self))
            self.tool_radiobtns[i].clicked.connect(self.OnPaintToolClicked)
            toolgb_layout.addWidget(self.tool_radiobtns[i])

        self.tool_radiobtns[0].setChecked(True)
        self.paintTool = 0
        paintgb_layout.addWidget(toolgb)

        settinggb = QGroupBox('설정')
        setting_layout = QGridLayout()
        settinggb.setLayout(setting_layout)

        paintgb_layout.addWidget(settinggb)

        setting_layout.addWidget(QLabel('선 굵기'), 0, 0)
        self.line_combo = QComboBox()
        [self.line_combo.addItem(str(i)) for i in range(1, 21)]
        setting_layout.addWidget(self.line_combo, 0, 1)

        setting_layout.addWidget(QLabel('선 색상'), 1, 0)
        self.pencolor = QColor(0, 0, 0)
        self.penbtn = QPushButton()
        self.penbtn.setStyleSheet('background-color: rgb(0,0,0)')
        self.penbtn.clicked.connect(self.showColorDlg)
        setting_layout.addWidget(self.penbtn, 1, 1)

        setting_layout.addWidget(QLabel('채우기 색상'), 2, 0)
        self.brushcolor = QColor(0, 0, 0)
        self.brushbtn = QPushButton()
        self.brushbtn.setStyleSheet('background-color: rgba(0,0,0,255)')
        self.brushbtn.clicked.connect(self.showColorDlg)
        setting_layout.addWidget(self.brushbtn, 2, 1)

        setting_layout.addWidget(QLabel('글꼴'), 3, 0)
        self.font = QFont()
        self.font_btn = QPushButton('{}'.format(self.font.family()))
        self.font_btn.clicked.connect(self.showFontDlg)
        setting_layout.addWidget(self.font_btn, 3, 1)



        transgb = QGroupBox('변형')
        transgb.setFixedWidth(300)
        trans_layout = QGridLayout()
        transgb.setLayout(trans_layout)
        trn = ['밝기', '회전', 'fps', '압축', '노이즈', 'resize', '공백']
        self.trn_chk = []
        for n, i in enumerate(trn[:6]):
            chk = QCheckBox()
            trans_layout.addWidget(chk, n, 0)
            self.trn_chk.append(chk)
            trans_layout.addWidget(QLabel(i), n, 1)

        self.br_s = QSpinBox()
        self.br_s.setValue(0)
        self.br_s.setRange(-255, 255)
        trans_layout.addWidget(self.br_s, 0, 5)

        self.ro_s = QSpinBox()
        self.ro_s.setValue(0)
        self.ro_s.setRange(0, 360)
        trans_layout.addWidget(self.ro_s, 1, 5)

        self.fps_s = QSpinBox()
        self.fps_s.setMinimum(0)
        trans_layout.addWidget(self.fps_s, 2, 5)

        self.comp_s = QSpinBox()
        self.comp_s.setValue(100)
        self.comp_s.setRange(0, 101)
        trans_layout.addWidget(self.comp_s, 3, 5)

        self.noise_s = QDoubleSpinBox()
        self.noise_s.setRange(0, 1.0)
        trans_layout.addWidget(self.noise_s, 4, 5)

        self.resize_s_w = QLineEdit()
        self.resize_s_h = QLineEdit()
        trans_layout.addWidget(QLabel('width'), 6, 1)
        trans_layout.addWidget(self.resize_s_w, 6, 2)
        trans_layout.addWidget(QLabel('height'), 6, 3)
        trans_layout.addWidget(self.resize_s_h, 6, 4)

        chk = QCheckBox()
        trans_layout.addWidget(chk, 7, 0)
        self.trn_chk.append(chk)
        trans_layout.addWidget(QLabel('PiP'), 7, 1)
        self.pip_l = QLineEdit()
        self.pip_t = QLineEdit()
        self.pip_r = QLineEdit()
        self.pip_b = QLineEdit()
        trans_layout.addWidget(self.pip_l, 8, 1)
        trans_layout.addWidget(self.pip_t, 8, 2)
        trans_layout.addWidget(self.pip_r, 8, 3)
        trans_layout.addWidget(self.pip_b, 8, 4)
        apply_tran = QPushButton('apply')

        trans_layout.addWidget(apply_tran, 8, 5)
        apply_tran.clicked.connect(self.apply_transform)

        queryEditor_layout.addWidget(transgb)
        queryEditor_layout.addWidget(paintgb)

        mainForm.addWidget(queryEditor)

        self.setLayout(mainForm)

        self.upload_btn.clicked.connect(self.OnUploadBtnClicked)
        self.frameExtractor.finished.connect(self.FinishExtractFrames)
        self.frameTable_selectioModel.selectionChanged.connect(self.selectFrames)
        self.frameTable_filter_combobox.currentIndexChanged.connect(self.OnFrameTableFiltercomboBoxChanged)
        self.toQueryEditorBtn.clicked.connect(self.OnToQueryEditorBtnClicked)

    def ChangeBrightness(self, bg, val):
        hsv = cv2.cvtColor(bg, cv2.COLOR_BGR2HSV)
        v = hsv[:, :, 2]
        if val > 0:
            lim = 255 - val
            v[v > lim] = 255
            v[v <= lim] += val
        else:
            lim = -val
            v[v < lim] = 0
            v[v >= lim] -= lim
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def Rotate(self, bg, val):
        height, width, channel = bg.shape
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), val, 1)
        return cv2.warpAffine(bg, matrix, (width, height))

    def Compress(self, bg, val):
        result, encimg = cv2.imencode('.jpg', bg, [int(cv2.IMWRITE_JPEG_QUALITY), val])
        return encimg

    def sp_noise(self, bg, val):
        thres = 1 - val
        for i in range(bg.shape[0]):
            for j in range(bg.shape[1]):
                rdn = random.random()
                if rdn < val:
                    bg[i][j] = 0
                elif rdn > thres:
                    bg[i][j] = 255
        return bg

    def apply_transform(self):
        paint = self.savePaint()
        bg = cv2.imread(self.origin)
        if self.trn_chk[0].isChecked():
            bg = self.ChangeBrightness(bg, self.br_s.value())
        if self.trn_chk[1].isChecked():
            bg = self.Rotate(bg, self.ro_s.value())

        if self.trn_chk[3].isChecked():
            bg = self.Compress(bg, self.comp_s.value())

        if self.trn_chk[4].isChecked():
            bg = self.sp_noise(bg, self.noise_s.value())
        if self.trn_chk[5].isChecked():
            bg = cv2.resize(bg, (int(self.resize_s_w.text()), int(self.resize_s_h.text())))
            paint = cv2.resize(paint,(int(self.resize_s_w.text()), int(self.resize_s_h.text())))

        cv2.imwrite('./tmp/transform.jpg', bg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        self.ToBackground('./tmp/transform.jpg')
        paint = cv2.resize(paint, (self.display_w,self.display_h))
        self.paint.scene.addPixmap(cvtMat2QPix(paint))

    def savePaint(self):
        QPixmap(self.paint.grab()).save(self.paint_im)
        self.paint.scene.clear()
        return cv2.imread(self.paint_im, cv2.IMREAD_UNCHANGED)

    def OnPaintToolClicked(self):
        for i in range(len(self.tool_radiobtns)):
            if self.tool_radiobtns[i].isChecked():
                self.paintTool = i
                break

    def showFontDlg(self):
        sender = self.sender()
        font, ok = QFontDialog().getFont()
        if ok:
            self.font = font
            self.font_btn.setText('{}'.format(self.font.family()))

    def showColorDlg(self):
        # 색상 대화상자 생성
        sender = self.sender()

        # 색상 대화상자 생성
        if sender == self.penbtn:
            color = QColorDialog().getColor()
        elif sender == self.brushbtn:
            color = QColorDialog().getColor(options=QColorDialog.ShowAlphaChannel)

        # 색상이 유효한 값이면 참, QFrame에 색 적용
        if sender == self.penbtn and color.isValid():
            self.pencolor = color
            l = color.name(QColor.HexArgb)[1:]
            a = int(l[:2], base=16)
            r = int(l[2:4], base=16)
            g = int(l[4:6], base=16)
            b = int(l[6:], base=16)
            print(r, g, b, a, )
            self.penbtn.setStyleSheet('background-color: rgb({},{},{})'.format(r, g, b))
        else:
            self.brushcolor = color
            l = color.name(QColor.HexArgb)[1:]
            a = int(l[:2], base=16)
            r = int(l[2:4], base=16)
            g = int(l[4:6], base=16)
            b = int(l[6:], base=16)
            self.brushbtn.setStyleSheet('background-color: rgba({},{},{},{})'.format(r, g, b, a))

    def ToBackground(self, path):
        csize = self.query_container.size()
        cw = csize.width()
        ch = csize.height()
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        self.origin_h, self.origin_w, c = im.shape

        rw = cw / self.origin_w
        rh = ch / self.origin_h
        r = rw if rw <= rh else rh
        self.display_w = int(self.origin_w * r)
        self.display_h = int(self.origin_h * r)
        o = cv2.resize(im, (self.display_w, self.display_h))
        cv2.imwrite(self.bg_im, o, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

        style = "background:url({}) no-repeat center;".format(self.bg_im.replace('\\', '/'))
        style += "border:0px solid rgb(0, 255, 0);"
        self.query_container.setStyleSheet(style)

        margin_top = (ch - self.display_h) / 2
        margin_left = (cw - self.display_w) / 2
        self.query_container_layout.setContentsMargins(margin_left, margin_top, margin_left, margin_top)
        self.paint.setFixedHeight(self.display_h)
        self.paint.setFixedWidth(self.display_w)
        self.paint.scene.clear()

        return margin_left, margin_top

    def OnToQueryEditorBtnClicked(self):
        l = os.listdir(self.tmp_frame_dir)
        start = int(self.selected_filter_start.text())
        end = int(self.selected_filter_end.text())
        frame_idx = min(max(0, int((end - start + 1) / 2) + start), len(l) - 1)
        self.origin = os.path.join(self.tmp_frame_dir, l[frame_idx])
        print('[Selected Represent Frame] {}'.format(self.origin))
        self.ToBackground(os.path.join(self.tmp_frame_dir, l[frame_idx]))

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
        self.selected_filter_start.setText('0')
        self.selected_filter_end.setText('0')
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
        print('[Delete Rows]')
        # self.model.setRowCount(0)
        self.model.clear()
        self.initFrameTableSetting()

    def initFrameTableSetting(self):
        self.model.setHorizontalHeaderLabels(['Thumbnail', 'start', 'end', 'path'])
        header = self.frameTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

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


if __name__ == '__main__':
    from App import MyApp

    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
