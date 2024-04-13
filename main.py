# -*- coding:utf-8 -*-
import sys
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow, isDarkTheme,
                            NavigationPushButton)
from qfluentwidgets import FluentIcon as FIF
from src.servo_interface import ServoInterface
from src.camera_interface import CameraInterface
from src.main_interface import MainInterface

from src.face_detect_interface import FaceDetector
from src.servo_manager import ServoManager
from src.camera_manager import CameraManager


class Window(MSFluentWindow):
    # stop_servo_ctl_sign = pyqtSignal()
    # stop_camera_ctl_sign = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 加载配置文件
        self.settings = QSettings("config/setting.ini", QSettings.IniFormat)

        # 初始化人脸识别检测器
        self.face_detector = FaceDetector("weights/FaceBoxes.pth")
        # 初始化舵机驱动
        self.servo_manager = ServoManager()
        # 初始化相机驱动
        self.camera_manager = CameraManager()

        # 添加子界面
        self.mainInterface = MainInterface(self.face_detector, self.camera_manager, self.servo_manager, self)
        self.cameraInterface = CameraInterface(self.face_detector, self.camera_manager, self)
        self.servoInterface = ServoInterface(self.servo_manager, self)

        self.initNavigation()
        self.initWindow()
        self.connectSignSlots()

    def connectSignSlots(self):
        self.mainInterface.stop_debug_camera.connect(self.cameraInterface.stopCamera)
        self.mainInterface.stop_debug_servo.connect(self.servoInterface.stopServo)

        self.mainInterface.sys_running_sign.connect(self.sysRunningSlot)

    def sysRunningSlot(self, f):
        if f:
            self.stackedWidget.widget(1).setEnabled(False)
            self.stackedWidget.widget(2).setEnabled(False)
        else:
            self.stackedWidget.widget(1).setEnabled(True)
            self.stackedWidget.widget(2).setEnabled(True)

    def initNavigation(self):
        self.addSubInterface(self.mainInterface, FIF.HOME, '主程序')
        self.addSubInterface(self.cameraInterface, FIF.ALBUM, '调试图像')
        self.addSubInterface(self.servoInterface, FIF.ROBOT, '调试舵机')

        self.navigationInterface.addItem(
            routeKey='avatar',
            icon='resource/image/avatar.png',
            text='Cola',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.addItem(
            routeKey='themeInterface',
            icon=FIF.BRIGHTNESS,
            text='明亮模式',
            position=NavigationItemPosition.BOTTOM,
            onClick=self.changeTheme,
            selectable=False,
        )

        self.navigationInterface.setCurrentItem(self.mainInterface.objectName())

    def changeTheme(self):
        if isDarkTheme():
            setTheme(Theme.LIGHT)
            m_text = "明亮模式"
            m_icon = FIF.BRIGHTNESS
            self.settings.setValue("ThemeMode", 0)
        else:
            setTheme(Theme.DARK)
            m_text = "夜间模式"
            m_icon = FIF.CONSTRACT
            self.settings.setValue("ThemeMode", 1)
        theme_it = self.navigationInterface.items["themeInterface"]
        if isinstance(theme_it, NavigationPushButton):
            theme_it._text = m_text
            theme_it._icon = m_icon

    def initWindow(self):
        # 缩放界面，设置界面图标和标题，移动到屏幕中间
        self.resize(1000, 800)
        self.setWindowIcon(QIcon('resource/image/logo.png'))
        self.setWindowTitle('Face Tracker')
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()

        if self.settings.value("ThemeMode") == "0":
            setTheme(Theme.LIGHT)
            m_text = "明亮模式"
            m_icon = FIF.BRIGHTNESS
        else:
            setTheme(Theme.DARK)
            m_text = "夜间模式"
            m_icon = FIF.CONSTRACT
        theme_it = self.navigationInterface.items["themeInterface"]
        if isinstance(theme_it, NavigationPushButton):
            theme_it._text = m_text
            theme_it._icon = m_icon
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def showMessageBox(self):
        w = MessageBox(
            '项目介绍🍜',
            '该项目全称为基于视觉的人脸追踪云台,涵盖软件/硬件/算法等三大部分,用于实现实时的人脸追踪,广泛应用于迎宾/安防/导购等诸多与人👨交互的应用场景.\n如果觉得该项目做的还行,请点个赞呗🌼~',
            self
        )
        w.yesButton.setText(' 👍 * 10086')
        w.cancelButton.setText(' 👎 * 99999')
        w.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置高分屏 高dpi
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    w = Window()
    w.show()
    app.exec_()
