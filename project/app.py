
import sys
import typing
from PyQt6 import QtCore
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QHBoxLayout
import socket, struct
import pandas as pd
import pyqtgraph as pg

class RedPitayaSensor:
    def __init__(self):
        self.buffer_size = 65536
        self.size_of_raw_adc = 16384
        self.msg_from_client = "-a 1"
        self.bytes_to_send = str.encode(self.msg_from_client)
        self.server_address_port = ("192.168.128.1", 61231)
        # Create a UDP socket at client side
        self.udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # Send to server using created UDP socket
        self.send_msg_to_server()

    def send_msg_to_server(self):
        self.udp_client_socket.sendto(self.bytes_to_send, self.server_address_port)

    def get_data_from_server(self):
        packet = self.udp_client_socket.recv(self.buffer_size)
        print(f"Total Received : {len(packet)} Bytes.")
        header_length = int(struct.unpack('@f', packet[:4])[0])
        ultrasonic_data_length = int(struct.unpack('@f', packet[4:8])[0])
        header_data = []
        for i in struct.iter_unpack('@f', packet[:header_length]):
            header_data.append(i[0])
        ultrasonic_data = []
        for i in struct.iter_unpack('@h', packet[header_length:]):
            ultrasonic_data.append(i[0])
        print(f"Length of Header : {len(header_data)}")
        print(f"Length of Ultrasonic Data : {len(ultrasonic_data)}")
        df = pd.DataFrame(ultrasonic_data, columns=['raw_adc'])
        return df["raw_adc"]

rp_sensor = RedPitayaSensor()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.button_is_checked = True

        self.setWindowTitle("My App")

        self.plot_widget = pg.PlotWidget()
        
        self.plot_adc_data()
        
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot_widget, 0, 0)
        self.range_selector.sigRegionChangeFinished.connect(self.region_changed_on_linear_region)

        # for button
        self.button = QPushButton("Press Me!")
        self.button.setCheckable(True)
        # button.clicked.connect(self.the_button_was_clicked)
        self.button.clicked.connect(self.the_button_was_toggled)
        self.button.setChecked(self.button_is_checked)
        self.button.setFixedSize(QSize(40,40))

        self.bottom_layout = QHBoxLayout()

        self.bottom_layout.addWidget(self.button)
        
        self.confirm_selection_button = QPushButton("Confirm")
        self.bottom_layout.addWidget(self.confirm_selection_button)

        self.dummy_button1 = QPushButton("Confirm")
        self.bottom_layout.addWidget(self.dummy_button1)

        self.dummy_button2 = QPushButton("Confirm")
        self.bottom_layout.addWidget(self.dummy_button2)

        main_layout.addLayout(self.bottom_layout, 1, 0)


        self.widget = QWidget()
        self.widget.setLayout(main_layout)
        self.setCentralWidget(self.widget)

    def region_changed_on_linear_region(self):
        print("Region Changed!")
        print(self.range_selector.getRegion())

    def the_button_was_toggled(self, checked):
        self.button_is_checked = checked
        print("Checked", self.button_is_checked)
        self.button.setText(f"Status: {self.button_is_checked}")
        self.plot_adc_data()

    def plot_adc_data(self):
        self.plot_widget.clear()
        if not self.button_is_checked:
            # Generate some example data
            x = [i for i in range(rp_sensor.size_of_raw_adc)]
            y = x
        else:
            x = [i for i in range(rp_sensor.size_of_raw_adc)]
            y = rp_sensor.get_data_from_server().to_list()
        # Plot the data
        self.plot = self.plot_widget.plot(x, y)
        self.plot_widget.setBackground('black')
        self.range_selector = pg.LinearRegionItem()
        print(self.range_selector.getRegion())
        self.plot_widget.addItem(self.range_selector)



app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()