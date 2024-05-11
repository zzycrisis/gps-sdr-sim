import csv
import subprocess
import sys
from PyQt5.QtCore import QRectF, Qt, QPropertyAnimation, pyqtProperty, \
    QPoint, QParallelAnimationGroup, QEasingCurve
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QApplication, \
    QLineEdit, QPushButton
import numpy as np


class BubbleLabel(QWidget):
    BackgroundColor = QColor(195, 195, 195)
    BorderColor = QColor(150, 150, 150)

    def __init__(self, *args, **kwargs):
        text = kwargs.pop("text", "")
        super(BubbleLabel, self).__init__(*args, **kwargs)
        # 设置无边框置顶
        self.setWindowFlags(
            Qt.Window | Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        # 设置最小宽度和高度
        self.setMinimumWidth(200)
        self.setMinimumHeight(48)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        layout = QVBoxLayout(self)
        # 左上右下的边距（下方16是因为包括了三角形）
        layout.setContentsMargins(8, 8, 8, 16)
        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.setText(text)
        # 获取屏幕高宽
        self._desktop = QApplication.instance().desktop()

    def setText(self, text):
        self.label.setText(text)

    def text(self):
        return self.label.text()

    def stop(self):
        self.hide()
        self.animationGroup.stop()
        self.close()

    def show(self):
        super(BubbleLabel, self).show()
        # 窗口开始位置
        startPos = QPoint(
            self._desktop.screenGeometry().width() - self.width() - 100,
            self._desktop.availableGeometry().height() - self.height())
        endPos = QPoint(
            self._desktop.screenGeometry().width() - self.width() - 100,
            self._desktop.availableGeometry().height() - self.height() * 3 - 5)
        print(startPos, endPos)
        self.move(startPos)
        # 初始化动画
        self.initAnimation(startPos, endPos)

    def initAnimation(self, startPos, endPos):
        # 透明度动画
        opacityAnimation = QPropertyAnimation(self, b"opacity")
        opacityAnimation.setStartValue(1.0)
        opacityAnimation.setEndValue(0.0)
        # 设置动画曲线
        opacityAnimation.setEasingCurve(QEasingCurve.InQuad)
        opacityAnimation.setDuration(4000)  # 在4秒的时间内完成
        # 往上移动动画
        moveAnimation = QPropertyAnimation(self, b"pos")
        moveAnimation.setStartValue(startPos)
        moveAnimation.setEndValue(endPos)
        moveAnimation.setEasingCurve(QEasingCurve.InQuad)
        moveAnimation.setDuration(5000)  # 在5秒的时间内完成
        # 并行动画组（目的是让上面的两个动画同时进行）
        self.animationGroup = QParallelAnimationGroup(self)
        self.animationGroup.addAnimation(opacityAnimation)
        self.animationGroup.addAnimation(moveAnimation)
        self.animationGroup.finished.connect(self.close)  # 动画结束时关闭窗口
        self.animationGroup.start()

    def paintEvent(self, event):
        super(BubbleLabel, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 抗锯齿

        rectPath = QPainterPath()  # 圆角矩形
        triPath = QPainterPath()  # 底部三角形

        height = self.height() - 8  # 往上偏移8
        rectPath.addRoundedRect(QRectF(0, 0, self.width(), height), 5, 5)
        x = self.width() / 5 * 4
        triPath.moveTo(x, height)  # 移动到底部横线4/5处
        # 画三角形
        triPath.lineTo(x + 6, height + 8)
        triPath.lineTo(x + 12, height)

        rectPath.addPath(triPath)  # 添加三角形到之前的矩形上

        # 边框画笔
        painter.setPen(QPen(self.BorderColor, 1, Qt.SolidLine,
                            Qt.RoundCap, Qt.RoundJoin))
        # 背景画刷
        painter.setBrush(self.BackgroundColor)
        # 绘制形状
        painter.drawPath(rectPath)
        # 三角形底边绘制一条线保证颜色与背景一样
        painter.setPen(QPen(self.BackgroundColor, 1,
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(x, height, x + 12, height)

    def windowOpacity(self):
        return super(BubbleLabel, self).windowOpacity()

    def setWindowOpacity(self, opacity):
        super(BubbleLabel, self).setWindowOpacity(opacity)

    # 由于opacity属性不在QWidget中需要重新定义一个
    opacity = pyqtProperty(float, windowOpacity, setWindowOpacity)


class Window(QWidget):

    def __init__(self, *args, **kwargs):
        #super(Window, self).__init__(*args, **kwargs)
        super().__init__()
        # layout = QVBoxLayout(self)
        # self.msgEdit = QLineEdit(self, returnPressed=self.onMsgShow)
        # self.msgButton = QPushButton("显示内容", self, clicked=self.onMsgShow)
        # layout.addWidget(self.msgEdit)
        # layout.addWidget(self.msgButton)
        self.onMsgShow()

    def onMsgShow(self):
        msg = "bin文件已生成!"
        if not msg:
            return
        if hasattr(self, "_blabel"):
            self._blabel.stop()
            self._blabel.deleteLater()
            del self._blabel
        self._blabel = BubbleLabel()
        self._blabel.setText(msg)
        self._blabel.show()

def loadCmd():
    # 指定工作目录
    work_dir = "D:/python/pyQt/spoofing"

    with open('points.txt', 'r') as f:
        points=f.read()
    last=points[-1]
    for point in points:
        if point is last:
            point=point.replace('\n','')
            g_bin="\ngps-sdr-sim -e brdc1700.19n -l "+point+",100\n"
            # 打开一个命令行进程
            proc = subprocess.Popen('cmd', stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, cwd=work_dir)
            # 向命令行发送命令
            stdout, stderr = proc.communicate(g_bin)
            # 输出命令执行的结果和错误
            print('命令行:', stdout.strip())  # 使用 strip() 去除多余的空格和换行
            print('输出:', stderr)
            break
        else:
            ps=np.loadtxt('points.txt')
            y=ps[:,0]
            x=ps[:,1]
            num=len(ps)#数组长度
            time=0.0
            with open('points.csv', 'w') as w:
                print("清除动态选点历史\n")
            with open('points.csv','a') as f:
                for i in range(num-1):#0到ps长度减2
                    x_sub=x[i+1]-x[i]
                    y_sub=y[i+1]-y[i]
                    x_sub/=10
                    y_sub/=10
                    cnt=0
                    t="%.1f"%time
                    f.write(t + ", " + str(x[i]) + ", " + str(y[i]) + ", " + str(100) + '\n')
                    time+=0.1
                    while cnt!=10:
                        x_tmp=x[i]+cnt*x_sub
                        y_tmp=y[i]+cnt*y_sub
                        t = "%.2f" % time
                        f.write(t+", "+str(x_tmp)+", "+str(y_tmp)+", "+str(100)+'\n')
                        time+=0.1
                        cnt+=1
            g_bin = "\ngps-sdr-sim -e brdc1700.19n -x points.csv\n"
            # 打开一个命令行进程
            proc = subprocess.Popen('cmd', stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, cwd=work_dir)
            # 向命令行发送命令
            stdout, stderr = proc.communicate(g_bin)
            # 输出命令执行的结果和错误
            print('命令行:', stdout.strip())  # 使用 strip() 去除多余的空格和换行
            print('输出:', stderr)
            break
    return True
if __name__=='__main__':
    if loadCmd():
        app = QApplication(sys.argv)
        w = Window()
        w.show()
        sys.exit(app.exec_())