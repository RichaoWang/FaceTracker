# -*- coding: utf-8 -*-
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QTimer, QSettings
from threading import Thread
from qfluentwidgets import FluentIcon, PushButton, PlainTextEdit, LineEdit, ComboBox, BodyLabel, setFont, MessageBox

from view.ui_servo import Ui_servo
from src.servo_manager import ServoEnum

"""
    舵机调试界面
"""


class ServoInterface(Ui_servo, QWidget):
    log_sign = pyqtSignal(int, str, name="log_sign")  # 日志信号 0-正常 1-异常 2-错误
    update_angle_sign = pyqtSignal()

    def __init__(self, servo_manager, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self._settings = QSettings("config/setting.ini", QSettings.IniFormat)

        # 属性变量
        self._isConnect = False
        self._isRandom = False
        self._servoManager = servo_manager

        self.upButton.setIcon(FluentIcon.UP)
        self.downButton.setIcon(FluentIcon.DOWN)
        self.leftButton.setIcon(FluentIcon.LEFT_ARROW)
        self.rightButton.setIcon(FluentIcon.RIGHT_ARROW)

        # 设置按钮对应的快捷键
        self.upButton.setShortcut("up")
        self.downButton.setShortcut("down")
        self.leftButton.setShortcut("left")
        self.rightButton.setShortcut("right")

        # ----------- 设置set card widget内容 -----------
        self.setCard.setTitle("帮助&设置")
        self.setCard.headerView.setFixedHeight(40)

        rotup_lay = QHBoxLayout(self)
        rotup_lb1 = BodyLabel("当前上部舵机转角:", self)
        self.rotup_lb2 = BodyLabel("0", self)
        rotup_lay.addWidget(rotup_lb1)
        rotup_lay.addWidget(self.rotup_lb2)
        setFont(rotup_lb1, 11)
        setFont(self.rotup_lb2, 11)
        self.setCard.viewLayout.addLayout(rotup_lay)

        rotbt_lay = QHBoxLayout(self)
        rotbt_lb1 = BodyLabel("当前底部舵机转角:", self)
        self.rotbt_lb2 = BodyLabel("0", self)
        rotbt_lay.addWidget(rotbt_lb1)
        rotbt_lay.addWidget(self.rotbt_lb2)
        setFont(rotbt_lb1, 11)
        setFont(self.rotbt_lb2, 11)
        self.setCard.viewLayout.addLayout(rotbt_lay)

        self.setCard.viewLayout.setDirection(QBoxLayout.Direction.TopToBottom)  # 设置方向从上至下排列
        self.link_btn = PushButton("连接舵机", self)
        self.setCard.viewLayout.addWidget(self.link_btn)

        self.reset_btn = PushButton("舵机复位", self)
        self.setCard.viewLayout.addWidget(self.reset_btn)

        self.test_btn = PushButton("开启随机性测试", self)
        self.setCard.viewLayout.addWidget(self.test_btn)

        unit_step_ang_lay = QHBoxLayout(self)
        unit_step_ang_lb = BodyLabel("单位步进角度", self)
        self.unit_step_ang_le = LineEdit(self)
        self.unit_step_ang_le.setText("20")
        self.unit_step_ang_le.setPlaceholderText("0~180°")
        unit_step_ang_lay.addWidget(unit_step_ang_lb)
        unit_step_ang_lay.addWidget(self.unit_step_ang_le)
        self.setCard.viewLayout.addLayout(unit_step_ang_lay)

        speed_lay = QHBoxLayout(self)
        speed_label = BodyLabel("速度模式", self)
        speed_lay.setAlignment(Qt.AlignCenter)
        self.speed_cb = ComboBox(self)
        self.speed_cb.addItems(["高速", "中速", "低速"])
        speed_lay.addWidget(speed_label)
        speed_lay.addWidget(self.speed_cb)
        self.setCard.viewLayout.addLayout(speed_lay)

        bottom_servo_ang_lay = QHBoxLayout(self)
        self.bottom_servo_ang_le = LineEdit(self)
        self.bottom_servo_ang_le.setPlaceholderText("底部转角(0~180°)")
        self.bottom_servo_ang_btn = PushButton("发送", self)
        bottom_servo_ang_lay.addWidget(self.bottom_servo_ang_le)
        bottom_servo_ang_lay.addWidget(self.bottom_servo_ang_btn)
        self.setCard.viewLayout.addLayout(bottom_servo_ang_lay)

        upper_servo_ang_lay = QHBoxLayout(self)
        self.upper_servo_ang_le = LineEdit(self)
        self.upper_servo_ang_le.setPlaceholderText("上部转角(0~180°)")
        self.upper_servo_ang_btn = PushButton("发送", self)
        upper_servo_ang_lay.addWidget(self.upper_servo_ang_le)
        upper_servo_ang_lay.addWidget(self.upper_servo_ang_btn)
        self.setCard.viewLayout.addLayout(upper_servo_ang_lay)
        # ---------------------------------------------

        help_text_ed = PlainTextEdit(self)
        # help_text_ed.setMaximumHeight(350)
        help_text_ed.setReadOnly(True)
        html_text = """
                <html>
                    <body>
                        <p><strong><font size="5">使用说明: \n</font></strong></p>
                        <p>● 连接舵机后,使用电脑快捷键(上下左右)即可进行舵机控制; \n</p>
                        <p>● 点击舵机复位,即可使舵机恢复默认初始位置; \n</p>
                        <p>● 通过设置下拉框速度选项,可选择不同的速度模式; \n</p>
                        <p>● 通过编辑两部分舵机的转角值,舵机可直接旋转至目标角度. \n</p>
                        <p>● 日志等级解释 黑:正常;黄:警告;红:异常. \n</p>
                    </body>
                </html>
                """
        help_text_ed.document().setHtml(html_text)
        help_text_ed.setFocusPolicy(Qt.NoFocus)
        help_text_ed.setMinimumHeight(200)
        self.setCard.viewLayout.addWidget(help_text_ed)

        # 设置阴影
        self.setShadowEffect(self.ctlCard)
        self.setShadowEffect(self.setCard)
        self.setShadowEffect(self.logPlainTextEdit)

        self.logPlainTextEdit.setReadOnly(True)

        # 在未连接舵机的情况下，除了连接按钮，其他控件都不可用
        self.controlEnable(False)

        # 定时器刷新angler
        self._timer = QTimer(self)

        # 连接槽函数
        self.connectSignSlots()

    def controlEnable(self, is_ctl, is_random_test=False):
        for i in self.findChildren(QPushButton):
            if is_random_test:
                if i != self.test_btn:
                    i.setEnabled(is_ctl)
            else:
                if i != self.link_btn:
                    i.setEnabled(is_ctl)
        for i in [self.upButton, self.downButton, self.leftButton, self.rightButton]:
            i.setEnabled(is_ctl)
        self.unit_step_ang_le.setEnabled(is_ctl)
        self.bottom_servo_ang_le.setEnabled(is_ctl)
        self.upper_servo_ang_le.setEnabled(is_ctl)

    def connectSignSlots(self):
        self.upButton.clicked.connect(self.moveUp)
        self.downButton.clicked.connect(self.moveDown)
        self.leftButton.clicked.connect(self.moveLeft)
        self.rightButton.clicked.connect(self.moveRight)
        self.link_btn.clicked.connect(self.connectServo)
        self.test_btn.clicked.connect(self.testServo)
        self.reset_btn.clicked.connect(self.resetServo)
        self.bottom_servo_ang_btn.clicked.connect(self.bottomServoAngSlot)
        self.upper_servo_ang_btn.clicked.connect(self.UpperServoAngSlot)

        self.unit_step_ang_le.editingFinished.connect(self.unitStepAngSlot)
        self.bottom_servo_ang_le.editingFinished.connect(self.bottomServoAngLESlot)
        self.upper_servo_ang_le.editingFinished.connect(self.upperServoAngLESlot)

        self._timer.timeout.connect(self.timerSlot)

        self.log_sign.connect(self.logSlot)
        self.update_angle_sign.connect(self.updateAngleSlot)

    def timerSlot(self):
        self.rotup_lb2.setText(str(self._servoManager.getVerticalServoAngle()))
        self.rotbt_lb2.setText(str(self._servoManager.getHorizontalServoAngle()))

    def upperServoAngLESlot(self):
        try:
            val = int(self.upper_servo_ang_le.text())
        except ValueError as e:
            self.log_sign.emit(1, "上部舵机转角输入框只允许输入整数类型")
            self.upper_servo_ang_le.setText("")
            return
        if not 0 <= val <= 180:
            self.log_sign.emit(1, "上部舵机转角区间为0-180°.")
            self.upper_servo_ang_le.setText("")

    def bottomServoAngLESlot(self):
        try:
            val = int(self.bottom_servo_ang_le.text())
        except ValueError as e:
            self.log_sign.emit(1, "底部舵机转角输入框只允许输入整数类型")
            self.bottom_servo_ang_le.setText("")
            return
        if not 0 <= val <= 180:
            self.log_sign.emit(1, "底部舵机转角区间为0-180°.")
            self.bottom_servo_ang_le.setText("")

    def bottomServoAngSlot(self):
        if self.speed_cb.currentIndex() == 0:
            speed = 100
        elif self.speed_cb.currentIndex() == 1:
            speed = 500
        else:
            speed = 1000
        self._servoManager.singleRotation(ServoEnum.HORIZONTAL, int(self.bottom_servo_ang_le.text()), speed)
        self.bottom_servo_ang_le.clear()
        self.update_angle_sign.emit()

    def UpperServoAngSlot(self):
        if self.speed_cb.currentIndex() == 0:
            speed = 100
        elif self.speed_cb.currentIndex() == 1:
            speed = 500
        else:
            speed = 1000
        self._servoManager.singleRotation(ServoEnum.VERTICAL, int(self.upper_servo_ang_le.text()), speed)
        self.upper_servo_ang_le.clear()
        self.update_angle_sign.emit()

    def updateAngleSlot(self):
        self.rotup_lb2.setText(str(self._servoManager.getVerticalServoAngle()))
        self.rotbt_lb2.setText(str(self._servoManager.getHorizontalServoAngle()))

    def unitStepAngSlot(self):
        try:
            val = int(self.unit_step_ang_le.text())
        except ValueError as e:
            self.log_sign.emit(1, "单位步进角度只允许输入整数类型")
            self.unit_step_ang_le.setText("1")
            return
        if not 0 <= val <= 180:
            self.log_sign.emit(1, "输入的单位步进角度,区间为0-180°")
            self.unit_step_ang_le.setText("1")

    def logSlot(self, idx, msg):
        cur_time = QDateTime.currentDateTime().toString("yyyy-MM-dd-hh:mm:ss")  # 获取当前时间
        if idx == 0:
            display_msg = """
                            <html>
                            <body>
                            <p><strong>{}: {}</strong></p>
                            </body>
                            </html>
                            """.format(cur_time, msg)
        elif idx == 1:
            display_msg = """
                         <html>
                         <body>
                         <p><strong><span style="color:orange;">{}: [警告] {}</span></strong></p>
                         </body>
                         </html>
                         """.format(cur_time, msg)
        else:
            display_msg = """
                         <html>
                         <body>
                         <p><strong><span style="color:red;">{}: [异常] {}</span></strong></p>
                         </body>
                         </html>
                         """.format(cur_time, msg)
        self.logPlainTextEdit.appendHtml(display_msg)

    def resetServo(self):
        if not self._servoManager.resetAllServos():
            self.log_sign.emit(2, "舵机复位失败,检查bug？")
            return
        self.log_sign.emit(0, "舵机复位.")
        self.update_angle_sign.emit()

    def stopServo(self):
        """
        切换page时停止 *前提是做了舵机存活检测*
        :return:
        """
        if self._isRandom:
            self.testServo()
        self.connectServo()

    def testServo(self):
        if self._isRandom:
            self.test_btn.setText("开启随机性测试")
            self.log_sign.emit(0, "关闭随机性测试.")
            self._timer.stop()
            self._servoManager.stopRandomTest()
            # self._servoManager.resetAllServos()
            self.controlEnable(True, True)
            self.update_angle_sign.emit()
        else:
            self.test_btn.setText("关闭随机性测试")
            self.log_sign.emit(0, "开启随机性测试.")
            if self.speed_cb.currentIndex() == 0:
                speed = 100
            elif self.speed_cb.currentIndex() == 1:
                speed = 500
            else:
                speed = 1000
            t = Thread(target=self._servoManager.startRandomTest, args=(speed,))
            t.setDaemon(True)
            t.start()
            self._timer.start(500)
            self.controlEnable(False, True)
        self._isRandom = not self._isRandom

    def connectServo(self):
        if self._isConnect:
            self._servoManager.disconnectSerial()
            self.link_btn.setText("连接舵机")
            self.log_sign.emit(0, "断开连接舵机.")
            self.controlEnable(False)
            self.rotup_lb2.setText("0")
            self.rotbt_lb2.setText("0")
        else:
            is_suc = self._servoManager.connectSerial(self._settings.value("ServoIdx"))
            if not is_suc:
                w = MessageBox(
                    '串口打开失败',
                    '请检查串口是否插入设备上,或者串口号(当前:{})是否错误!\n查询串口号方法:设备管理器->端口(COM和LPT)->USB-SERIAL CH340(COM?).\n'
                    '确定好端口号后,请更新端口号到config/setting.ini下的ServoIdx的字段后.'.format(
                        self._settings.value("ServoIdx")),
                    self
                )
                w.yesButton.setText('确定')
                w.cancelButton.setText('返回')
                w.exec()
                return

            self.link_btn.setText("断开连接舵机")
            self.log_sign.emit(0, "连接舵机.")
            self.controlEnable(True)
            self.update_angle_sign.emit()
        self._isConnect = not self._isConnect

    def moveUp(self):
        if self.speed_cb.currentIndex() == 0:
            speed = 100
        elif self.speed_cb.currentIndex() == 1:
            speed = 500
        else:
            speed = 1000
        issuc, msg = self._servoManager.moveUp(int(self.unit_step_ang_le.text()), speed)
        if issuc:
            self.log_sign.emit(0, "舵机上转,单次步进角度{}°,当前角度{}°.".format(self.unit_step_ang_le.text(), msg))
        else:
            self.log_sign.emit(1, "{}".format(msg))
        self.update_angle_sign.emit()

    def moveDown(self):
        if self.speed_cb.currentIndex() == 0:
            speed = 100
        elif self.speed_cb.currentIndex() == 1:
            speed = 500
        else:
            speed = 1000
        issuc, msg = self._servoManager.moveDown(int(self.unit_step_ang_le.text()), speed)
        if issuc:
            self.log_sign.emit(0, "舵机下转,单次步进角度{}°,当前角度{}°.".format(self.unit_step_ang_le.text(), msg))
        else:
            self.log_sign.emit(1, "{}".format(msg))
        self.update_angle_sign.emit()

    def moveLeft(self):
        if self.speed_cb.currentIndex() == 0:
            speed = 100
        elif self.speed_cb.currentIndex() == 1:
            speed = 500
        else:
            speed = 1000
        issuc, msg = self._servoManager.moveLeft(int(self.unit_step_ang_le.text()), speed)
        if issuc:
            self.log_sign.emit(0, "舵机左转,单次步进角度{}°,当前角度{}°.".format(self.unit_step_ang_le.text(), msg))
        else:
            self.log_sign.emit(1, "{}".format(msg))
        self.update_angle_sign.emit()

    def moveRight(self):
        if self.speed_cb.currentIndex() == 0:
            speed = 100
        elif self.speed_cb.currentIndex() == 1:
            speed = 500
        else:
            speed = 1000
        issuc, msg = self._servoManager.moveRight(int(self.unit_step_ang_le.text()), speed)
        print(issuc, msg)
        if issuc:
            self.log_sign.emit(0, "舵机右转,单次步进角度{}°,当前角度{}°.".format(self.unit_step_ang_le.text(), msg))
        else:
            self.log_sign.emit(1, "{}".format(msg))
        self.update_angle_sign.emit()

    def setShadowEffect(self, card: QWidget):
        shadowEffect = QGraphicsDropShadowEffect(self)
        shadowEffect.setColor(QColor(0, 0, 0, 100))
        shadowEffect.setBlurRadius(30)
        shadowEffect.setOffset(0, 0)
        card.setGraphicsEffect(shadowEffect)
