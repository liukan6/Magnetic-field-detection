import sys
import serial
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QGridLayout, QInputDialog, QMessageBox
from PyQt5.QtGui import QFont

class MagneticFieldVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ser = None
        self.calibration_complete = False  
        
        selected_port = self.show_port_selection_dialog()
        if selected_port:
            self.init_serial(selected_port)
        else:
            self.ser = None  
        
        self.max_points = 200
        self.time_data = np.arange(self.max_points)
        self.data_buffers = {
            'BX': np.zeros(self.max_points),
            'BY': np.zeros(self.max_points),
            'BZ': np.zeros(self.max_points),
            'RX': np.zeros(self.max_points),
            'RY': np.zeros(self.max_points),
            'SZ': np.zeros(self.max_points),
            'FX': np.zeros(self.max_points),
            'FY': np.zeros(self.max_points),
            'FZ': np.zeros(self.max_points)
        }
        
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(50)  
        
    def show_port_selection_dialog(self):
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            reply = QMessageBox.question(
                None,
                '未找到串口',
                '未检测到任何串口设备。\n\n是否以模拟数据模式运行？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                print("用户选择以模拟数据模式运行")
                return None
            else:
                print("用户取消运行")
                sys.exit(0)
        
        port_options = []
        port_dict = {}
        for port in ports:
            display_name = f"{port.device} - {port.description}"
            port_options.append(display_name)
            port_dict[display_name] = port.device
            print(f"发现串口: {display_name}")
        
        port_options.append("模拟数据模式（无硬件）")
        
        item, ok = QInputDialog.getItem(
            None,
            '选择串口',
            '请选择要连接的串口：',
            port_options,
            0,
            False
        )
        
        if ok and item:
            if item == "模拟数据模式（无硬件）":
                print("用户选择模拟数据模式")
                return None
            else:
                selected_port = port_dict[item]
                print(f"用户选择串口: {selected_port}")
                return selected_port
        else:
            print("用户取消选择")
            sys.exit(0)
    
    def find_available_ports(self):
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        available = []
        for port in ports:
            available.append(port.device)
            print(f"发现串口: {port.device} - {port.description}")
        return available
    
    def init_serial(self, port):
        try:
            self.ser = serial.Serial(port, 115200, timeout=1)
            print(f"成功连接到串口: {port}")
        except Exception as e:
            QMessageBox.warning(
                None,
                '连接失败',
                f'无法连接到串口 {port}\n\n错误: {e}\n\n程序将以模拟数据模式运行。',
                QMessageBox.Ok
            )
            self.ser = None
    
    def init_ui(self):
        self.setWindowTitle("MLX90393 磁场传感器实时监控")
        self.setGeometry(100, 100, 1600, 1000)
        
        font = QFont()
        font.setFamily("Microsoft YaHei UI")  
        font.setPointSize(10)
        QApplication.setFont(font)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #f5f7fa;")
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel("磁场力实时监测系统 - 等待校准...")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                padding: 18px;
                background-color: #2563eb;
                border: none;
                border-radius: 10px;
            }
        """)
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QtGui.QColor(37, 99, 235, 100))
        shadow.setOffset(0, 4)
        self.title_label.setGraphicsEffect(shadow)
        main_layout.addWidget(self.title_label)
        
        self.value_labels = self.create_value_display()
        main_layout.addWidget(self.value_labels)
        
        charts_container = QWidget()
        charts_layout = QHBoxLayout(charts_container)
        charts_layout.setSpacing(10)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget_left = pg.GraphicsLayoutWidget()
        self.plot_widget_left.setBackground('#ffffff')
        charts_layout.addWidget(self.plot_widget_left, stretch=3)
        
        self.plot_widget_right = pg.GraphicsLayoutWidget()
        self.plot_widget_right.setBackground('#ffffff')
        charts_layout.addWidget(self.plot_widget_right, stretch=2)
        
        main_layout.addWidget(charts_container, stretch=3)  
        
        self.create_plots()
        
    def create_value_display(self):
        value_widget = QWidget()
        layout = QHBoxLayout(value_widget)  
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.labels = {}
        fields = [
            ('BX', '磁场X', 'uT'), ('BY', '磁场Y', 'uT'), ('BZ', '磁场Z', 'uT'),
            ('FX', '力FX', 'N'), ('FY', '力FY', 'N'), ('FZ', '力FZ', 'N')
        ]
        
        for key, text, unit in fields:
            card = QWidget()
            card_layout = QHBoxLayout(card)  
            card_layout.setContentsMargins(15, 12, 15, 12)
            card_layout.setSpacing(15)
            
            label_name = QLabel(text)
            label_name.setAlignment(QtCore.Qt.AlignCenter)
            label_name.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 18px;
                    font-weight: 600;
                    background-color: #3b82f6;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            label_name.setMinimumWidth(90)
            
            label_value = QLabel("0.00")
            label_value.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            label_value.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    font-size: 26px;
                    font-weight: 600;
                    background-color: transparent;
                    font-family: 'Consolas', 'Courier New', monospace;
                }
            """)
            label_value.setMinimumWidth(160)
            
            card_layout.addWidget(label_name)
            card_layout.addWidget(label_value)
            
            card.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    border: 2px solid #3b82f6;
                    border-radius: 10px;
                }
            """)
            card_shadow = QtWidgets.QGraphicsDropShadowEffect()
            card_shadow.setBlurRadius(10)
            card_shadow.setColor(QtGui.QColor(59, 130, 246, 60))
            card_shadow.setOffset(0, 2)
            card.setGraphicsEffect(card_shadow)
            
            layout.addWidget(card)
            self.labels[key] = (label_value, unit) 
        
        value_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        return value_widget
    
    def create_plots(self):
        axis_style = {'color': '#5a6c7d', 'font-size': '11pt'}
        
        font = QFont('Microsoft YaHei UI', 10)
        
        self.plot1 = self.plot_widget_left.addPlot(row=0, col=0)
        self.plot1.setTitle("<span style='color: #2563eb; font-size: 16pt; font-weight: 600;'>原始磁场强度 (Bx, By, Bz)</span>")
        self.plot1.addLegend(labelTextColor='#5a6c7d', brush=(255, 255, 255, 230), pen={'color': '#e8ecf0', 'width': 1})
        
        self.curve_bx = self.plot1.plot(pen=pg.mkPen(color='#ff0080', width=2), name="Bx")
        self.curve_by = self.plot1.plot(pen=pg.mkPen(color='#00ff80', width=2), name="By")
        self.curve_bz = self.plot1.plot(pen=pg.mkPen(color='#00d4ff', width=2), name="Bz")
        
        self.plot1.setLabel('left', '磁场强度 (uT)', **axis_style)
        self.plot1.setLabel('bottom', '时间 (samples)', **axis_style)
        self.plot1.showGrid(x=True, y=True, alpha=0.15)
        self.plot1.getAxis('left').setPen('#d0d7de')
        self.plot1.getAxis('bottom').setPen('#d0d7de')
        self.plot1.getAxis('left').setTextPen('#5a6c7d')
        self.plot1.getAxis('bottom').setTextPen('#5a6c7d')
        self.plot1.getAxis('left').setStyle(tickFont=font)
        self.plot1.getAxis('bottom').setStyle(tickFont=font)
        self.plot1.setXRange(0, 200, padding=0)
        self.plot1.setMouseEnabled(x=False, y=True)
        self.plot1.enableAutoRange(axis='x', enable=False)
        self.plot1.enableAutoRange(axis='y', enable=False)
        
        self.plot_widget_left.nextRow()
        
        self.plot2 = self.plot_widget_left.addPlot(row=1, col=0)
        self.plot2.setTitle("<span style='color: #2563eb; font-size: 16pt; font-weight: 600;'>计算力总图 (FX, FY, FZ)</span>")
        self.plot2.addLegend(labelTextColor='#5a6c7d', brush=(255, 255, 255, 230), pen={'color': '#e8ecf0', 'width': 1})
        
        self.curve_fx_combined = self.plot2.plot(pen=pg.mkPen(color='#5470c6', width=2.5), name="FX")  
        self.curve_fy_combined = self.plot2.plot(pen=pg.mkPen(color='#91cc75', width=2.5), name="FY") 
        self.curve_fz_combined = self.plot2.plot(pen=pg.mkPen(color='#fac858', width=2.5), name="FZ") 
        
        self.plot2.setLabel('left', '力值 (N)', **axis_style)
        self.plot2.setLabel('bottom', '时间 (samples)', **axis_style)
        self.plot2.showGrid(x=True, y=True, alpha=0.15)
        self.plot2.getAxis('left').setPen('#d0d7de')
        self.plot2.getAxis('bottom').setPen('#d0d7de')
        self.plot2.getAxis('left').setTextPen('#5a6c7d')
        self.plot2.getAxis('bottom').setTextPen('#5a6c7d')
        self.plot2.getAxis('left').setStyle(tickFont=font)
        self.plot2.getAxis('bottom').setStyle(tickFont=font)
        self.plot2.setXRange(0, 200, padding=0)
        self.plot2.setMouseEnabled(x=False, y=True)
        self.plot2.enableAutoRange(axis='x', enable=False)
        self.plot2.enableAutoRange(axis='y', enable=False)
        
        self.plot_widget_left.ci.layout.setRowStretchFactor(0, 1)
        self.plot_widget_left.ci.layout.setRowStretchFactor(1, 1)
        
        self.plot3 = self.plot_widget_right.addPlot(row=0, col=0)
        self.plot3.setTitle("<span style='color: #2563eb; font-size: 16pt; font-weight: 600;'>力FX</span>")
        self.curve_fx = self.plot3.plot(pen=pg.mkPen(color='#5470c6', width=2.5))
        
        self.plot3.setLabel('left', 'FX (N)', **axis_style)
        self.plot3.setLabel('bottom', '时间 (samples)', **axis_style)
        self.plot3.showGrid(x=True, y=True, alpha=0.15)
        self.plot3.getAxis('left').setPen('#d0d7de')
        self.plot3.getAxis('bottom').setPen('#d0d7de')
        self.plot3.getAxis('left').setTextPen('#5a6c7d')
        self.plot3.getAxis('bottom').setTextPen('#5a6c7d')
        self.plot3.getAxis('left').setStyle(tickFont=font)
        self.plot3.getAxis('bottom').setStyle(tickFont=font)
        self.plot3.setXRange(0, 200, padding=0)
        self.plot3.setMouseEnabled(x=False, y=True)
        self.plot3.enableAutoRange(axis='x', enable=False)
        self.plot3.enableAutoRange(axis='y', enable=False)
        
        self.plot_widget_right.nextRow()
        
        self.plot4 = self.plot_widget_right.addPlot(row=1, col=0)
        self.plot4.setTitle("<span style='color: #2563eb; font-size: 16pt; font-weight: 600;'>力FY</span>")
        self.curve_fy = self.plot4.plot(pen=pg.mkPen(color='#91cc75', width=2.5)) 
        
        self.plot4.setLabel('left', 'FY (N)', **axis_style)
        self.plot4.setLabel('bottom', '时间 (samples)', **axis_style)
        self.plot4.showGrid(x=True, y=True, alpha=0.15)
        self.plot4.getAxis('left').setPen('#d0d7de')
        self.plot4.getAxis('bottom').setPen('#d0d7de')
        self.plot4.getAxis('left').setTextPen('#5a6c7d')
        self.plot4.getAxis('bottom').setTextPen('#5a6c7d')
        self.plot4.getAxis('left').setStyle(tickFont=font)
        self.plot4.getAxis('bottom').setStyle(tickFont=font)
        self.plot4.setXRange(0, 200, padding=0)
        self.plot4.setMouseEnabled(x=False, y=True)
        self.plot4.enableAutoRange(axis='x', enable=False)
        self.plot4.enableAutoRange(axis='y', enable=False)
        
        self.plot_widget_right.nextRow()
        
        self.plot5 = self.plot_widget_right.addPlot(row=2, col=0)
        self.plot5.setTitle("<span style='color: #2563eb; font-size: 16pt; font-weight: 600;'>力FZ</span>")
        self.curve_fz = self.plot5.plot(pen=pg.mkPen(color='#fac858', width=2.5)) 
        
        self.plot5.setLabel('left', 'FZ (N)', **axis_style)
        self.plot5.setLabel('bottom', '时间 (samples)', **axis_style)
        self.plot5.showGrid(x=True, y=True, alpha=0.15)
        self.plot5.getAxis('left').setPen('#d0d7de')
        self.plot5.getAxis('bottom').setPen('#d0d7de')
        self.plot5.getAxis('left').setTextPen('#5a6c7d')
        self.plot5.getAxis('bottom').setTextPen('#5a6c7d')
        self.plot5.getAxis('left').setStyle(tickFont=font)
        self.plot5.getAxis('bottom').setStyle(tickFont=font)
        self.plot5.setXRange(0, 200, padding=0)
        self.plot5.setMouseEnabled(x=False, y=True)
        self.plot5.enableAutoRange(axis='x', enable=False)
        self.plot5.enableAutoRange(axis='y', enable=False)
        
        self.plot_widget_right.ci.layout.setRowStretchFactor(0, 1)
        self.plot_widget_right.ci.layout.setRowStretchFactor(1, 1)
        self.plot_widget_right.ci.layout.setRowStretchFactor(2, 1)
    
    def parse_serial_data(self, line):
        try:
            data = {}
            decoded_line = line.decode('utf-8', errors='ignore').strip()
            
            if '校准中' in decoded_line:
                print(f"校准中: {decoded_line}")
                return None 
            
            if '校准完成' in decoded_line or '开始输出数据' in decoded_line:
                self.calibration_complete = True
                self.title_label.setText("磁场力实时监测系统")
                print("校准完成，开始显示数据")
                return None
            
            if not self.calibration_complete:
                return None
            
            parts = decoded_line.split()
            
            i = 0
            while i < len(parts):
                part = parts[i]
                if part in ['BX:', 'BY:', 'BZ:', 'RX:', 'RY:', 'SZ:']:
                    if i + 1 < len(parts):
                        try:
                            key = part.replace(':', '')
                            data[key] = float(parts[i + 1])
                        except ValueError:
                            pass
                    i += 2
                elif part == 'FX' and i + 1 < len(parts) and parts[i + 1] != 'FY':
                    try:
                        data['FX'] = float(parts[i + 1])
                    except ValueError:
                        pass
                    i += 2
                elif part == 'FY' and i + 1 < len(parts) and parts[i + 1] != 'FZ':
                    try:
                        data['FY'] = float(parts[i + 1])
                    except ValueError:
                        pass
                    i += 2
                elif part == 'FZ' and i + 1 < len(parts):
                    try:
                        data['FZ'] = float(parts[i + 1])
                    except ValueError:
                        pass
                    i += 2
                else:
                    i += 1
            
            return data
        except Exception as e:
            print(f"数据解析错误: {e}")
            return None
    
    def update_data_buffers(self, data):
        for key in self.data_buffers.keys():
            if key in data:
                self.data_buffers[key] = np.roll(self.data_buffers[key], -1)
                
                self.data_buffers[key][-1] = data[key]
    
    def _adjust_y_range(self, plot, data_arrays, min_range=0.1):
        all_data = np.concatenate(data_arrays)
        data_min = np.min(all_data)
        data_max = np.max(all_data)
        data_range = data_max - data_min
        
        if data_range < min_range:
            center = (data_max + data_min) / 2
            data_min = center - min_range / 2
            data_max = center + min_range / 2
        
        padding = (data_max - data_min) * 0.1
        plot.setYRange(data_min - padding, data_max + padding, padding=0)
    
    def update_plots(self):
        self.curve_bx.setData(self.time_data, self.data_buffers['BX'])
        self.curve_by.setData(self.time_data, self.data_buffers['BY'])
        self.curve_bz.setData(self.time_data, self.data_buffers['BZ'])
        self._adjust_y_range(self.plot1, [self.data_buffers['BX'], self.data_buffers['BY'], self.data_buffers['BZ']], min_range=50)
        
        self.curve_fx_combined.setData(self.time_data, self.data_buffers['FX'])
        self.curve_fy_combined.setData(self.time_data, self.data_buffers['FY'])
        self.curve_fz_combined.setData(self.time_data, self.data_buffers['FZ'])
        self._adjust_y_range(self.plot2, [self.data_buffers['FX'], self.data_buffers['FY'], self.data_buffers['FZ']], min_range=2)
        
        self.curve_fx.setData(self.time_data, self.data_buffers['FX'])
        self._adjust_y_range(self.plot3, [self.data_buffers['FX']], min_range=1)
        
        self.curve_fy.setData(self.time_data, self.data_buffers['FY'])
        self._adjust_y_range(self.plot4, [self.data_buffers['FY']], min_range=1)
        
        self.curve_fz.setData(self.time_data, self.data_buffers['FZ'])
        self._adjust_y_range(self.plot5, [self.data_buffers['FZ']], min_range=1)
    
    def update_value_labels(self, data):
        for key, (label, unit) in self.labels.items():
            if key in data:
                label.setText(f"{data[key]:>7.2f} {unit}")
    
    def update_data(self):
        if self.ser and self.ser.in_waiting:
            try:
                line = self.ser.readline()
                data = self.parse_serial_data(line)
                
                if data and self.calibration_complete:
                    self.update_data_buffers(data)
                    self.update_plots()
                    self.update_value_labels(data)
                    
            except Exception as e:
                print(f"数据读取错误: {e}")
        elif self.ser is None:
            import random
            simulated_data = {
                'BX': random.uniform(-10, 10),
                'BY': random.uniform(-10, 10),
                'BZ': random.uniform(-300, -290),
                'RX': random.uniform(-0.1, 0.1),
                'RY': random.uniform(-0.1, 0.1),
                'SZ': random.uniform(0, 1),
                'FX': random.uniform(0, 10),
                'FY': random.uniform(0, 10),
                'FZ': random.uniform(0, 20)
            }
            self.update_data_buffers(simulated_data)
            self.update_plots()
            self.update_value_labels(simulated_data)

def main():
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    
    window = MagneticFieldVisualizer()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()