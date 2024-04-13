# -*- coding:utf-8 -*-

import serial
from enum import Enum
import random
import time

"""
ServoManager 用于控制*舵机转角*

    其与下位机为串口通讯，一个协议例子为以下：
           #1P2500T100\r\n
        通讯协议解析：
        数字 1 为舵机控制板上的 S1 通道；
        数字 1500 是控制舵机的角度（范围为 500-2500），控制舵机的 0-180 度；
        数字 100 是时间，时间的意思是，从当前的位置，旋转到命令中的位置，所需要的时间。
    
    *上部舵机接在开发板S1口*    *底部舵机接在开发板S2口*
"""


class ServoEnum(Enum):
    """
    枚举舵机类型
    本项目仅有两个舵机：
    HORIZONTAL代表底部舵机，VERTICAL代表上部舵机
    """
    VERTICAL = 1  # 竖向舵机（上部）
    HORIZONTAL = 2  # 横向舵机（底部）


class ServoManager(object):
    def __init__(self):
        self.serial = None
        self.vertical_servo_angle = 0
        self.horizontal_servo_angle = 0
        self._is_random = False

    def isAlive(self):
        """
        servo是否已经开启
        :return:
        """
        if self.serial is None:
            return False
        if self.serial.is_open:
            return True
        return False

    def connectSerial(self, port="COM4"):
        """
        连接串口
        :return:
        """
        if self.serial is not None:
            return
        try:
            self.serial = serial.Serial(port, 9600)  # todo 不知道com4会不会变？
        except Exception as e:
            print(e)
            return False
        if not self.serial.is_open:
            self.serial = None
            return False
        self.resetAllServos()
        return True

    def disconnectSerial(self):
        """
        断开连接串口
        :return:
        """
        if self.serial is not None:
            self.serial.close()
            self.serial = None

    def resetAllServos(self):
        """
        舵机回归初始位置
        :return:
        """
        if self.serial is not None:
            self.multiRotation(110, 90)
            self.vertical_servo_angle = 110
            self.horizontal_servo_angle = 90
            return True
        return False

    def _angler2Value(self, angle):
        """
        角度转下位机旋转值
        :return:
        """
        min_angle, max_angle, min_value, max_value = 0, 180, 500, 2500
        # 确保输入角度在合理范围内
        angle = max(min(angle, max_angle), min_angle)
        # 计算斜率和截距
        slope = (max_value - min_value) / (max_angle - min_angle)
        intercept = min_value - slope * min_angle
        # 计算输出值
        mapped_value = slope * angle + intercept
        return int(mapped_value)

    def _waitRead(self):
        self.serial.flush()
        self.serial.readline()

    def getVerticalServoAngle(self):
        """
        上部电机角度
        :return:
        """
        return self.vertical_servo_angle

    def getHorizontalServoAngle(self):
        """
        底部电机角度
        :return:
        """
        return self.horizontal_servo_angle

    def singleRotation(self, servo_enum: ServoEnum, angle: int, speed: int = 100):
        """
        舵机单独控制
        其协议如下：
            #1P2500T100\r\n
        数据 1 是舵机的通道
        数据 1500 是舵机的位置，范围是500-2500
        数据 100 是执行的时间，表示速度，范围是100-9999
        :param servo_enum:
        :param angle:
        :param speed:
        :return:
        """
        send_str = "#{}P{}T{}\r\n".format(servo_enum.value, self._angler2Value(angle), speed)
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()
        if servo_enum == ServoEnum.HORIZONTAL:
            self.horizontal_servo_angle = angle
        else:
            self.vertical_servo_angle = angle

    def multiRotation(self, angle2v: int, angle2h: int, speed: int = 100):
        """
        舵机并行控制
        其协议如下：
            #1P600#2P900#8P2500T100\r\n
        数据 1，2，8 是舵机的通道
        数据 600,900,2500 分别是 3 个通道的舵机的位置
        数据 100 是执行时间，是 3 个舵机的速度，不管舵机的数量是多少，时间只能有一个，也就是 T 只能有一个。该命令是同时执行的，也就是所有的舵机都是一起动的。

        :param angle2v:
        :param angle2h:
        :param speed:
        :return:
        """
        send_str = "#1P{}#2P{}T{}\r\n".format(self._angler2Value(angle2v), self._angler2Value(angle2h), speed)
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()
        self.vertical_servo_angle = angle2v
        self.horizontal_servo_angle = angle2h

    def moveA(self, x_step: int, y_step: int, speed: int = 100):
        """

        :param x_step: +x代表向下 -x代表向上
        :param y_step:
        :param speed:
        :return:
        """
        x_ang = self.getHorizontalServoAngle() + x_step
        y_ang = self.getVerticalServoAngle() + y_step
        if x_ang > 180 or x_ang < 0 or y_ang > 180 or y_ang < 0:
            return False, "存在舵机超行程."
        send_str = "#1P{}#2P{}T{}\r\n".format(self._angler2Value(y_ang), self._angler2Value(x_ang), speed)
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()
        self.vertical_servo_angle = y_ang
        self.horizontal_servo_angle = x_ang
        return True, ""

    def moveUp(self, step: int, speed: int = 100):
        ang = self.getVerticalServoAngle() - step
        if ang < 0:
            return False, "上部舵机超行程,最小有效旋转角:0°,当前:{}°.".format(ang)
        send_str = "#1P{}T{}\r\n".format(self._angler2Value(ang), speed)
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()
        self.vertical_servo_angle = ang
        return True, "{}".format(self.vertical_servo_angle)

    def moveDown(self, step: int, speed: int = 100):
        ang = self.getVerticalServoAngle() + step
        if ang > 180:
            return False, "上部舵机超行程,最大有效旋转角:180°,当前:{}°.".format(ang)
        send_str = "#1P{}T{}\r\n".format(self._angler2Value(ang), speed)
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()
        self.vertical_servo_angle = ang
        return True, "{}".format(self.vertical_servo_angle)

    def moveLeft(self, step: int, speed: int = 100):
        ang = self.getHorizontalServoAngle() - step
        if ang < 0:
            return False, "底部舵机超行程,最小有效旋转角:0°,当前:{}°.".format(ang)
        send_str = "#2P{}T{}\r\n".format(self._angler2Value(ang), speed)
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()
        self.horizontal_servo_angle = ang
        return True, "{}".format(self.horizontal_servo_angle)

    def moveRight(self, step: int, speed: int = 100):
        ang = self.getHorizontalServoAngle() + step
        if ang > 180:
            return False, "底部舵机超行程,最大有效旋转角:180°,当前:{}°.".format(ang)
        send_str = "#2P{}T{}\r\n".format(self._angler2Value(ang), speed)
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()
        self.horizontal_servo_angle = ang
        return True, "{}".format(self.horizontal_servo_angle)

    def startRandomTest(self, speed: int = 100):
        self._is_random = True
        while True:
            if not self._is_random:
                return
            v1 = random.randint(0, 180)
            v2 = random.randint(0, 180)
            self.multiRotation(v1, v2, 500)  # 不管传什么速度，都给500，否则可能欠压
            # print("v1: {}, v2: {}".format(v1, v2))
            # print("curV: {}, curH:{}".format(self.getVerticalServoAngle(), self.getHorizontalServoAngle()))
            time.sleep(0.3)

    def stop(self):
        """
        #STOP\r\n
        :return:
        """
        send_str = "#STOP\r\n"
        assert isinstance(self.serial, serial.Serial), ""
        self.serial.write(send_str.encode("utf-8"))
        self._waitRead()

    def stopRandomTest(self):
        self._is_random = False
        # self.stop()


if __name__ == '__main__':
    servo_man = ServoManager()
    servo_man.connectSerial("COM7")
    time.sleep(0.5)
    servo_man.moveA(10, 10, 50)
    # for _ in range(50):
    #     servo_man.singleRotation(ServoEnum.HORIZONTAL, 0)
    #     time.sleep(1)
    #     for _ in range(18):
    #         servo_man.moveRight(10)
    servo_man.disconnectSerial()
