# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import time

from PyQt5.QtGui import QColor, QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QSizePolicy
from PyQt5.QtCore import pyqtSignal, QSettings, Qt, QDateTime
from qfluentwidgets import setFont, MessageBox, PlainTextEdit
import cv2
from view.ui_main import Ui_Main
from src.servo_manager import ServoManager
from src.camera_manager import CameraManager
from src.trancking_plot1 import trancking_plot1
from src.trancking_plot2 import trancking_plot2

"""
    主程序界面
"""


class MainInterface(Ui_Main, QWidget):
    stop_debug_servo = pyqtSignal()
    stop_debug_camera = pyqtSignal()
    sys_running_sign = pyqtSignal(bool)
    face_tracking_sign = pyqtSignal(list)
    clear_view_sign = pyqtSignal()

    def __init__(self, face_detector, camera_manager, servo_manager, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.isRunning = False
        self.isTracking = False

        self.settings = QSettings("config/setting.ini", QSettings.IniFormat)

        self.face_detector = face_detector
        self.camera_manager = camera_manager
        self.servo_manager = servo_manager

        setFont(self.sysButton, 17)

        # 设置控件阴影
        self.setShadowEffect(self.frameview)
        self.setShadowEffect(self.CardWidget)
        self.setShadowEffect(self.CardWidget_2)
        self.setShadowEffect(self.ElevatedCardWidget)

        self.helpPlainTextEdit.setFocusPolicy(Qt.NoFocus)

        self.sysButton.setShortcut("space")

        # 设置帮助信息
        help_text = """
                        <html>
                            <body>
                                <p><strong><font size="5">使用说明: \n</font></strong></p>
                                <p>● 点击一键启动系统按钮,即可一键启动人脸识别及云台追踪功能; \n</p>
                                <p>● 系统启动中,会自动检测硬件设备是否已连接上,请根据提示进行断连或继续操作; \n</p>
                                <p>● 系统启动后,其他子界面将会暂停使用,控件将回归到初始状态; \n</p>
                                <p>● 点击关闭系统按钮,子界面将恢复可操作状态,系统暂停. \n</p>
                            </body>
                        </html>
                        """
        self.helpPlainTextEdit.document().setHtml(help_text)
        self.ElevatedCardWidget.setEnabled(False)

        # 连接槽函数
        self.connectSignSlots()

    def connectSignSlots(self):
        self.sysButton.clicked.connect(self.sysBtnClickedSlot)
        self.face_tracking_sign.connect(self.faceTracking, Qt.DirectConnection)

        self.clear_view_sign.connect(self.clearViewSlot, Qt.DirectConnection)

    def clearViewSlot(self):
        self.frameview.setPixmap(
            QPixmap("resource/image/trans.png").scaled(self.frameview.size(), aspectRatioMode=True))

    def faceTracking(self, info):
        assert isinstance(self.servo_manager, ServoManager)
        if not self.isRunning:
            return
        if self.plot1RadioButton.isChecked():
            trancking_plot1(info, self.servo_manager)
        else:
            trancking_plot2(info, self.servo_manager)

    def sysBtnClickedSlot(self):
        assert isinstance(self.servo_manager, ServoManager)
        assert isinstance(self.camera_manager, CameraManager)
        if self.isRunning:
            self.isRunning = False
            self.servo_manager.disconnectSerial()
            self.camera_manager.disconnect()
            time.sleep(0.3)  # todo 可能会有时序错乱问题，等一下
            while True:
                if (self.camera_manager.isAlive() + self.servo_manager.isAlive()) == 0:
                    self.camera_manager.update_frame_sign.disconnect()
                    break
                time.sleep(0.05)
            self.sys_running_sign.emit(False)
            self.clear_view_sign.emit()
            self.ElevatedCardWidget.setEnabled(False)
            self.sysButton.setText("一键启动系统")
        else:
            if self.servo_manager.isAlive() + self.camera_manager.isAlive() > 0:
                w = MessageBox(
                    '注意✋',
                    '检测到【舵机】或【相机】设备仍处于连接状态,设备再连接状态下无法一键启动系统.\n是否一键断开所有连接并启动系统?',
                    self
                )
                w.yesButton.setText('断开并启动')
                w.cancelButton.setText('返回')
                if w.exec() == 1:
                    self.stop_debug_servo.emit()
                    self.stop_debug_camera.emit()
                else:
                    return
            self.sys_running_sign.emit(True)
            self.isRunning = True
            self.servo_manager.connectSerial(self.settings.value("ServoIdx"))
            self.camera_manager.connect(int(self.settings.value("CamIdx")))
            self.camera_manager.update_frame_sign.connect(self.updateFrameSlot, Qt.DirectConnection)
            self.ElevatedCardWidget.setEnabled(True)
            self.sysButton.setText("暂停系统")

    def updateFrameSlot(self, frame):
        _frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # opencv读取的bgr格式图片转换成rgb格式
        _raw_frame = _frame.copy()
        # 推理
        res, keyp, _frame = self.face_detector.inference(_frame)
        h = _frame.shape[0]
        w = _frame.shape[1]
        cv2.line(_frame, (0, int(h / 2)), (w, int(h / 2)), (255, 0, 0), 1)
        cv2.line(_frame, (int(w / 2), 0), (int(w / 2), h), (0, 0, 255), 1)

        # 将关键点发出去
        if keyp:
            self.face_tracking_sign.emit([*keyp, _frame.shape[1], _frame.shape[0]])

        if self.debugviewSwitchButton.isChecked():
            _image = QImage(_frame[:], _frame.shape[1], _frame.shape[0], _frame.shape[1] * 3,
                            QImage.Format_RGB888)
        else:
            _image = QImage(_raw_frame[:], _raw_frame.shape[1], _raw_frame.shape[0], _raw_frame.shape[1] * 3,
                            QImage.Format_RGB888)
        _out = QPixmap(_image)
        # 调整图片尺寸以适应label大小，并更新label上的图片显示
        self.frameview.setPixmap(_out.scaled(self.frameview.size(), aspectRatioMode=True))

    def setShadowEffect(self, card: QWidget):
        shadowEffect = QGraphicsDropShadowEffect(self)
        shadowEffect.setColor(QColor(0, 0, 0, 100))
        shadowEffect.setBlurRadius(30)
        shadowEffect.setOffset(0, 0)
        card.setGraphicsEffect(shadowEffect)
