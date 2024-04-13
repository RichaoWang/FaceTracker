# Face Tracker

### 简介
```md
基于视觉检测的人脸识别追踪云台
* 相机获取图像帧并送入检测算法，获取人脸相对像素坐标的posx,posy;
* 舵机一个作用水平方向，一个作用垂直方向，通过得到检测结果，进行角度转换，通过串口通讯的方式控制舵机;
* 提供交互界面用于舵机，相机，算法的调试及启停。
```
---

### 部分截图
![42fc948d6ad0125665ec574c63eea20.jpg](doc%2F42fc948d6ad0125665ec574c63eea20.jpg)
![img.png](doc%2Fimg.png)![img_1.png](doc%2Fimg_1.png)![img_2.png](doc%2Fimg_2.png)

### 鸣谢
* FaceBoxes.PyTorch
* qfluentwidgets