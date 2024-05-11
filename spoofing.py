# coding:utf-8
import subprocess
import sys
import attack
import startCmd
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject, pyqtSlot, pyqtProperty, QRectF, QParallelAnimationGroup, \
    QEasingCurve, QPropertyAnimation, QPoint
from PyQt5.QtGui import QColor, QPen, QPainterPath, QPainter
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, \
    QGraphicsDropShadowEffect, QLabel, QDialog
from qfluentwidgets import SplitFluentWindow, RoundMenu, Action, \
    SplitPushButton, PushButton, FluentBackgroundTheme
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow.webengine import FramelessWebEngineView
class Printer(QObject):
    # pyqtSlot, 中文网络上大多称其为槽；其作用是接收网页发起的信号
    @pyqtSlot(str, result=str)
    def testTxt(self, content):
        print("输出经纬度:", content)
        with open('points.txt', 'a') as file:
            print("已打开文件")
            content=content.replace(',',' ')
            file.write(content)
            file.write('\n')
        return content

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


class Widget(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        #self.webView = QWebEngineView(self)
        self.webView = FramelessWebEngineView(self)
        self.webView.load(QUrl.fromLocalFile("/dynamic.html"))
        # 增加一个通信中需要用到的频道
        self.channel = QWebChannel()
        self.printer = Printer()# 通信过程中需要使用到的功能类
        # 将功能类注册到频道中，注册名可以任意，但将在网页中作为标识
        self.channel.registerObject("printer", self.printer)
        self.webView.page().setWebChannel(self.channel)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 40, 0, 0)
        self.vBoxLayout.addWidget(self.webView)
    def onload_finished(self,success):
        if success:
            print("loaded successful\n")
        else:
            print("failed to load\n")
    def load_url(self,url):
        print(url)
        self.webView.load(QUrl.fromLocalFile(url))
class Widget_1(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        #self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)
        self.pushButton = PushButtonDemo()

        #setFont(self.label, 24)
        #self.label.setAlignment(Qt.AlignCenter)
        #self.hBoxLayout.addWidget(self.label, 0, Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.pushButton, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))
        self.hBoxLayout.setContentsMargins(0, 40, 0, 0)

class ButtonView(QWidget):

    def __init__(self):
        super().__init__()
        #setTheme(Theme.DARK)
        #self.setStyleSheet("ButtonView{background: rgb(255,255,255)}")
class PushButtonDemo(ButtonView):
    menuActionTriggered = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.menu = RoundMenu(parent=self)
        action1=Action(FIF.ALBUM, '静态攻击')
        action2=Action(FIF.BASKETBALL, '动态攻击')
        self.menu.addAction(action1)
        self.menu.addAction(action2)

        self.splitPushButton1 = SplitPushButton('选择攻击方式', self)
        self.splitPushButton1.setFlyout(self.menu)
        self.pushButton1 = PushButton(FIF.SEND,'生成文件',self)
        self.pushButton1.clicked.connect(self.loadFunc)
        self.pushButton2=PushButton(FIF.AIRPLANE,'开始攻击',self)
        self.pushButton2.clicked.connect(self.start)
        self.pushButton3=PushButton(FIF.STOP_WATCH,'停止攻击',self)
        self.pushButton3.clicked.connect(self.stop)

        action1.triggered.connect(lambda: self.menuActionTriggered.emit('static'))
        action2.triggered.connect(lambda: self.menuActionTriggered.emit('dynamic'))

        self.gridLayout = QGridLayout(self)
        self.gridLayout.addWidget(self.splitPushButton1, 0, 0)
        self.gridLayout.addWidget(self.pushButton1, 1, 0)
        self.gridLayout.addWidget(self.pushButton2, 2, 0)
        self.gridLayout.addWidget(self.pushButton3, 3, 0)

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
    def loadFunc(self):
        print("调用生成bin函数")
        if startCmd.loadCmd():
            self.onMsgShow()
    def start(self):
        attack.start()
    def stop(self):
        attack.stop()


class Window(SplitFluentWindow):

    def __init__(self):
        super().__init__()

        # create sub interface
        self.mapInterface=Widget_1("mapInterface",self)
        self.homeInterface = Widget(self)
        self.mapInterface.pushButton.menuActionTriggered.connect(self.switch_map)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.mapInterface, FIF.ALBUM, "set")
        self.addSubInterface(self.homeInterface, FIF.HOME, "map")

        #self.setStyleSheet("background-color: #00000;")
        # NOTE: enable acrylic effect
        #self.navigationInterface.setAcrylicEnabled(True)

    def initWindow(self):
        self.resize(900, 700)
        #self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('GPS欺诈')
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        # use custom background color theme (only available when the mica effect is disabled)
        #self.setCustomBackgroundColor(*FluentBackgroundTheme.DEFAULT_BLUE)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint
                            | Qt.WindowMaximizeButtonHint)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
        self.setMicaEffectEnabled(False)

        # set the minimum window width that allows the navigation panel to be expanded
        # self.navigationInterface.setMinimumExpandWidth(900)
        # self.navigationInterface.expand(useAni=False)

    def switch_map(self, action):
        if action=='static':
            print("static")
            self.static=ChildWin("/test.html")

        elif action == 'dynamic':
            print("dynamic")
            self.dynamic=ChildWin("/dynamic.html")
class ChildWin(QDialog):
    def __init__(self,url):
        super().__init__()
        self.url=url
        self.initUI(self.url)
    def initUI(self,url):
        self.view = QWebEngineView()
        self.view.setWindowTitle("GPS攻击选点")
        self.view.resize(900, 600)
        # 增加一个通信中需要用到的频道
        self.channel = QWebChannel()
        # 通信过程中需要使用到的功能类
        self.printer = Printer()
        # 将功能类注册到频道中，注册名可以任意，但将在网页中作为标识
        self.channel.registerObject("printer", self.printer)
        # 在浏览器中设置该频道
        self.view.page().setWebChannel(self.channel)
        self.view.load(QUrl.fromLocalFile(url))
        self.view.show()
        with open('points.txt', 'w') as f:
            #清空文件内坐标点
            print("已清空历史选点信息")


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setTheme(Theme.DARK)

    app = QApplication(sys.argv)
    w = Window()

    w.show()
    w.setMicaEffectEnabled(False)
    app.exec_()
