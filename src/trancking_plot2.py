# -*- coding: utf-8 -*-
import numpy as np


def trancking_plot2(info, servo_manager):
    """
    策略二: 根据相机内参，计算x和y方向相对相机光心的差角
    todo 收敛巨慢,很难控制...
    """
    x, y, w, h = info
    mtx = np.array([[1.31922110e+03, 0.00000000e+00, 6.15777177e+02],
                    [0.00000000e+00, 1.32761156e+03, 3.73921249e+02],
                    [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
    kp = [x, y]
    def calculate_angle(mtx, pixel_coords):
        # 将像素坐标转换为相机坐标系中的坐标
        inv_mtx = np.linalg.inv(mtx)
        camera_coords = np.dot(inv_mtx, np.array([pixel_coords[0], pixel_coords[1], 1]))
        # 计算相对于相机坐标系中心的角度
        angle_x = np.arctan2(camera_coords[0], camera_coords[2])
        angle_y = np.arctan2(camera_coords[1], camera_coords[2])
        return int(np.degrees(angle_x)), int(np.degrees(angle_y))

    th = 5
    angle_x, angle_y = calculate_angle(mtx, kp)
    if abs(angle_x) >= th and abs(angle_y) >= th:
        servo_manager.moveA(angle_x, angle_y)
    elif abs(angle_x) >= th and abs(angle_y) < th:
        servo_manager.moveA(angle_x, 0)
    elif abs(angle_x) < th and abs(angle_y) >= th:
        servo_manager.moveA(0, angle_y)
    elif abs(angle_x) < th and abs(angle_y) < th:
        servo_manager.moveA(0, 0)
