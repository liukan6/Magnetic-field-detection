import sys
import serial
import serial.tools.list_ports
import numpy as np
import pyqtgraph as pg

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QInputDialog,
    QMessageBox
)

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont


class MagneticFieldVisualizer(QMainWindow):

    def __init__(self):
        super().__init__()

        self.ser = None

        self.max_points = 300

        self.timeData = np.arange(self.max_points)

        self.xData = np.zeros(self.max_points)
        self.yData = np.zeros(self.max_points)
        self.zData = np.zeros(self.max_points)

        port = self.selectPort()

        if port is not None:
            self.initSerial(port)

        self.initUI()

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateData)
        self.timer.start(10)

    # =========================================================
    # 串口选择
    # =========================================================
    def selectPort(self):

        ports = serial.tools.list_ports.comports()

        if len(ports) == 0:
            QMessageBox.warning(
                self,
                "错误",
                "未检测到串口"
            )
            sys.exit()

        portList = []
        portDict = {}

        for p in ports:
            text = f"{p.device}   {p.description}"
            portList.append(text)
            portDict[text] = p.device

        item, ok = QInputDialog.getItem(
            self,
            "选择串口",
            "请选择MLX90393串口：",
            portList,
            0,
            False
        )

        if ok and item:
            return portDict[item]

        sys.exit()

    # =========================================================
    # 初始化串口
    # =========================================================
    def initSerial(self, port):

        try:

            self.ser = serial.Serial(
                port,
                115200,
                timeout=1
            )

            print(f"已连接串口: {port}")

        except Exception as e:

            QMessageBox.warning(
                self,
                "串口错误",
                str(e)
            )

            sys.exit()

    # =========================================================
    # UI
    # =========================================================
    def initUI(self):

        self.setWindowTitle("MLX90393 实时磁场监测")

        self.resize(1400, 900)

        widget = QWidget()
        self.setCentralWidget(widget)

        layout = QVBoxLayout(widget)

        # =====================================================
        # 标题
        # =====================================================

        title = QLabel("MLX90393 三轴磁场实时监测")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
            color:white;
            background:#2563eb;
            padding:15px;
            border-radius:10px;
        """)

        layout.addWidget(title)

        # =====================================================
        # 数值显示
        # =====================================================

        font = QFont()
        font.setPointSize(20)

        self.labelX = QLabel("X: 0.00 uT")
        self.labelY = QLabel("Y: 0.00 uT")
        self.labelZ = QLabel("Z: 0.00 uT")

        for label in [self.labelX, self.labelY, self.labelZ]:

            label.setFont(font)

            label.setAlignment(Qt.AlignCenter)

            label.setStyleSheet("""
                background:white;
                border:2px solid #2563eb;
                border-radius:8px;
                padding:10px;
            """)

            layout.addWidget(label)

        # =====================================================
        # 绘图窗口
        # =====================================================

        self.plotWidget = pg.PlotWidget()

        self.plotWidget.setBackground("w")

        self.plotWidget.showGrid(x=True, y=True)

        self.plotWidget.setLabel("left", "磁场强度 (uT)")
        self.plotWidget.setLabel("bottom", "采样点")

        self.plotWidget.addLegend()

        layout.addWidget(self.plotWidget)

        # =====================================================
        # 三条曲线
        # =====================================================

        self.curveX = self.plotWidget.plot(
            pen=pg.mkPen("#ff0000", width=2),
            name="X"
        )

        self.curveY = self.plotWidget.plot(
            pen=pg.mkPen("#00aa00", width=2),
            name="Y"
        )

        self.curveZ = self.plotWidget.plot(
            pen=pg.mkPen("#0000ff", width=2),
            name="Z"
        )

    # =========================================================
    # 解析串口数据
    # =========================================================
    def parseLine(self, line):

        try:

            line = line.decode(
                "utf-8",
                errors="ignore"
            ).strip()

            # 示例:
            # 1234ms: 12.3 -5.6 88.9

            if "ms:" not in line:
                return None

            parts = line.split()

            if len(parts) < 4:
                return None

            tStr = parts[0]

            t = int(
                tStr.replace("ms:", "")
            )

            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])

            return t, x, y, z

        except:
            return None

    # =========================================================
    # 更新缓存
    # =========================================================
    def updateBuffers(self, x, y, z):

        self.xData = np.roll(self.xData, -1)
        self.yData = np.roll(self.yData, -1)
        self.zData = np.roll(self.zData, -1)

        self.xData[-1] = x
        self.yData[-1] = y
        self.zData[-1] = z

    # =========================================================
    # 自动调整Y轴
    # =========================================================
    def autoRange(self):

        allData = np.concatenate([
            self.xData,
            self.yData,
            self.zData
        ])

        ymin = np.min(allData)
        ymax = np.max(allData)

        if ymax - ymin < 1:
            ymax += 1
            ymin -= 1

        padding = (ymax - ymin) * 0.1

        self.plotWidget.setYRange(
            ymin - padding,
            ymax + padding
        )

    # =========================================================
    # 更新曲线
    # =========================================================
    def updatePlots(self):

        self.curveX.setData(
            self.timeData,
            self.xData
        )

        self.curveY.setData(
            self.timeData,
            self.yData
        )

        self.curveZ.setData(
            self.timeData,
            self.zData
        )

        self.autoRange()

    # =========================================================
    # 更新数值
    # =========================================================
    def updateLabels(self, x, y, z):

        self.labelX.setText(f"X: {x:.2f} uT")
        self.labelY.setText(f"Y: {y:.2f} uT")
        self.labelZ.setText(f"Z: {z:.2f} uT")

    # =========================================================
    # 主循环
    # =========================================================
    def updateData(self):

        if self.ser is None:
            return

        try:

            while self.ser.in_waiting:

                line = self.ser.readline()

                result = self.parseLine(line)

                if result is None:
                    continue

                t, x, y, z = result

                self.updateBuffers(x, y, z)

                self.updatePlots()

                self.updateLabels(x, y, z)

        except Exception as e:

            print(e)


# =============================================================
# 主函数
# =============================================================
def main():

    pg.setConfigOptions(antialias=True)

    app = QApplication(sys.argv)

    window = MagneticFieldVisualizer()

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()