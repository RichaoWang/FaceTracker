# -*- coding:utf-8 -*-
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
import time

"""
CameraManager 用于管理相机，获取图像帧
"""


class CameraManager(QThread):
    update_frame_sign = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._cap = None
        self._current_frame = np.ndarray([720, 1280, 3], dtype=np.uint8)
        self._mutex = QMutex()
        self._isConnect = False
        self._cam_idx = None
        self.start()

    def getCameraIndex(self):
        return self._cam_idx

    def isAlive(self):
        if self._cap is None:
            return False
        if not self._cap.isOpened:
            return False
        return True

    def connect(self, camera_id: int):
        if self._cap is not None:
            return False, "相机{}已启动.".format(self._cam_idx)
        try:
            self._cap = cv2.VideoCapture(camera_id)
            # 原生分辨率为640*480，提升到1280*720
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        except Exception as e:
            self._cap = None
            return False, "编号为 {} 的相机启动异常,报错信息 {}.".format(camera_id, e)
        if not self._cap.isOpened():
            self._cap = None
            del self._cap
            return False, "编号为 {} 的相机不能开启,请检查是否连接上设备.".format(camera_id)
        self._isConnect = True
        self._cam_idx = camera_id
        return True, ""

    def getFPS(self):
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        return fps

    def getFrameWH(self):
        return self._current_frame.shape[1], self._current_frame.shape[0]

    def run(self):
        while True:
            if not self._isConnect:
                time.sleep(0.05)
                continue
            if self._cap is None:
                time.sleep(0.05)
                continue
            self._mutex.lock()
            ret, frame = self._cap.read()
            if ret:
                self._current_frame = frame
                self.update_frame_sign.emit(cv2.flip(frame, 1))
            else:
                self.update_frame_sign.emit(cv2.flip(self._current_frame, 1))
            self._mutex.unlock()

    def disconnect(self):
        if self._cap is None:
            return
        self._isConnect = False
        self._cap.release()
        del self._cap
        self._cap = None

    def getFrame(self):
        return self._current_frame


if __name__ == '__main__':
    import time

    camera_man = CameraManager()
    camera_man.connect(1)
    while True:
        img=camera_man.getFrame()
        cv2.imshow("qwe",img)
        key =cv2.waitKey(1)
        if key==27:
            print("press esc exit")
            break
    # time.sleep(0.5)
    # print(type(camera_man.getFrame()))
    # cv2.imwrite("../test/test.jpg", camera_man.getFrame())
    # camera_man.disconnect()
