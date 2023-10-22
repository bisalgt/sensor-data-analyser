
import sys
from PyQt6.QtCore import QSize, Qt, QRunnable, pyqtSlot, QThreadPool, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QHBoxLayout, QCheckBox, QLabel
import socket, struct
import pandas as pd
import pyqtgraph as pg

from process_raw_adc import stft_of_complete_raw_adc



class RedPitayaSensor:
    def __init__(self):
        self.buffer_size = 65536
        self.size_of_raw_adc = 16384
        self.msg_from_client = "-a 1"
        self.bytes_to_send = str.encode(self.msg_from_client)
        self.server_address_port = ("192.168.128.1", 61231)
        # Create a UDP socket at client side
        self.sensor_status_message = "Waiting to Connect with RedPitaya UDP Server!"
        print(self.sensor_status_message)
        self.udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # Send to server using created UDP socket
        self.send_msg_to_server()

    def get_sensor_status_message(self):
        return self.sensor_status_message    

    def send_msg_to_server(self):
        self.udp_client_socket.sendto(self.bytes_to_send, self.server_address_port)

    def get_data_from_server(self):
        packet = self.udp_client_socket.recv(self.buffer_size)
        self.sensor_status_message = f"Sensor Connected Successfully at {self.server_address_port}!"
        print(self.sensor_status_message)
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



class Worker(QRunnable):
    '''
    Worker thread
    '''
    def __init__(self, func_is_button_checked, rp_sensor, *args, **kwargs) -> None:
        super().__init__()
        # self.realtime_checked = realtime_checked
        self.func_is_button_checked = func_is_button_checked
        self.rp_sensor = rp_sensor
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        print("Start of thread")
        while self.func_is_button_checked(*self.args, **self.kwargs):
            # self.fn(*self.args, **self.kwargs)
            try:
                result = self.rp_sensor.get_data_from_server()
            except:
                print("Some exception occured!")
            else:
                self.signals.result.emit(result)
            finally:
                print("One loop complete!")
            print(self.args, self.kwargs)
            # self.realtime_checked = self.func_is_button_checked(*self.args, **self.kwargs)
        

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported Signals are : 

    result
        data returned from rp sensor to plot on GUI
    '''

    result = pyqtSignal(object)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.rp_sensor = RedPitayaSensor()
        self.threadpool = QThreadPool()
        self.sensor_status_message = self.rp_sensor.get_sensor_status_message()

        self.button_is_checked = True
        self.realtime_chkbox_checked = False
        self.show_region_to_select = False
        self.raw_adc_data = None
        self.previous_range_selector_region = (100, 1000)

        self.setWindowTitle("Sensor Data Analyser")

        self.plot_widget = pg.PlotWidget()
        
        # self.plot_adc_data()
        
        main_layout = QGridLayout()
        main_layout.addWidget(self.plot_widget, 0, 0)
        

        # for button
        self.button = QPushButton("Press Me!")
        self.button.setCheckable(True)
        # button.clicked.connect(self.the_button_was_clicked)
        self.button.clicked.connect(self.the_button_was_toggled)
        self.button.setChecked(self.button_is_checked)
        self.button.setFixedSize(QSize(40,40))

        self.controls_mid_layout = QHBoxLayout()

        # self.controls_mid_layout.addWidget(self.button)
        
        self.realtime_chkbox = QCheckBox("Realtime")
        self.controls_mid_layout.addWidget(self.realtime_chkbox)

        self.show_region_chkbox = QCheckBox("Region-Select")
        self.controls_mid_layout.addWidget(self.show_region_chkbox)

        self.confirm_region_btn = QPushButton("Confirm")
        self.controls_mid_layout.addWidget(self.confirm_region_btn)

        main_layout.addLayout(self.controls_mid_layout, 1, 0)


        self.message_bottom_layout = QHBoxLayout()

        self.message_widget = QLabel(self.sensor_status_message)
        self.message_bottom_layout.addWidget(self.message_widget)

        main_layout.addLayout(self.message_bottom_layout, 2, 0)
        
        self.sensor_status_message = self.rp_sensor.get_sensor_status_message()
        self.message_widget.setText(self.sensor_status_message)

        self.widget = QWidget()
        self.widget.setLayout(main_layout)
        self.setCentralWidget(self.widget)

        
        # add Signal Handlers
        
        self.show_region_chkbox.stateChanged.connect(self.show_region_handler)
        self.realtime_chkbox.stateChanged.connect(self.realtime_checkbox_handler)
        self.confirm_region_btn.clicked.connect(self.confirm_region_selection_btn_handler)

    def show_region_handler(self,state):
        self.message_widget.setText(self.rp_sensor.get_sensor_status_message())
        if state == Qt.CheckState.Checked.value:
            print("Region select checked !")
            self.realtime_chkbox.setDisabled(True)
            self.confirm_region_btn.setDisabled(False)
            self.show_region_to_select = True
            # print(self.show_region_to_select)
            self.range_selector = pg.LinearRegionItem()
            self.range_selector.sigRegionChangeFinished.connect(self.region_changed_on_linear_region)
            self.range_selector.setRegion(self.previous_range_selector_region)
            print(self.range_selector.getRegion())
            self.plot_widget.addItem(self.range_selector)
        elif state == Qt.CheckState.Unchecked.value:
            self.reset_btn_view()
            self.plot_widget.removeItem(self.range_selector)

    def confirm_region_selection_btn_handler(self):
        if self.show_region_to_select:
            print("Confirmed Region : ", self.range_selector.getRegion())
            self.previous_range_selector_region = self.range_selector.getRegion()
            self.plot_adc_data()
            self.get_stft_of_complete_raw_adc()
            self.show_region_handler(self.show_region_chkbox.checkState().value)
            

    def reset_btn_view(self):
        self.realtime_chkbox.setDisabled(False)
        self.show_region_chkbox.setDisabled(False)
        self.confirm_region_btn.setDisabled(True)

    def region_changed_on_linear_region(self):
        print("Region Changed!")
        print(self.range_selector.getRegion())

    def the_button_was_toggled(self, checked):
        self.button_is_checked = checked
        print("Checked", self.button_is_checked)
        self.button.setText(f"Status: {self.button_is_checked}")
        self.plot_adc_data()

    def plot_adc_data(self, data=None):
        print(self.rp_sensor.get_sensor_status_message(), "------------------------------")
        self.message_widget.setText(self.rp_sensor.get_sensor_status_message())
        self.plot_widget.clear()
        # if self.button_is_checked:
        #     # Generate some example data
        #     x = [i for i in range(rp_sensor.size_of_raw_adc)]
        #     y = x
        # else:
        #     pass
        x = [i for i in range(self.rp_sensor.size_of_raw_adc)]
        if data is not None:
            y = data
        else:
            y = self.rp_sensor.get_data_from_server().to_list()
            # return
        # y = rp_sensor.get_data_from_server().to_list()

        self.raw_adc_data = y

        # Plot the data
        self.plot = self.plot_widget.plot(x, y)
        self.plot_widget.setBackground('black')
        print("Show region to select : ", self.range_selector.getRegion())
        if self.realtime_chkbox_checked == False:
            return False


    def realtime_checkbox_handler(self, state):
        
        if state == Qt.CheckState.Checked.value:
            self.realtime_chkbox_checked = True
            print("Go Realtime!")
            self.show_region_chkbox.setDisabled(True)
            self.confirm_region_btn.setDisabled(True)
            self.worker = Worker(self.func_is_realtime_checked, self.rp_sensor)
            self.worker.signals.result.connect(self.plot_adc_data)
            # start_index, end_index = self.range_selector.getRegion()
            # self.worker.signals.result.connect(self.get_stft_of_complete_raw_adc)
            self.threadpool.start(self.worker)
        else:
            self.realtime_chkbox_checked = False
            self.reset_btn_view()
        
    
    def func_is_realtime_checked(self):
        print("Checked : ", self.realtime_chkbox_checked)
        return self.realtime_chkbox_checked
    
    def get_stft_of_complete_raw_adc(self):
        print("INside STFT of app.py")
        if self.show_region_to_select:
            print("correct status stft------------------")
            start_index, end_index = self.range_selector.getRegion()
            stft_of_signal = stft_of_complete_raw_adc(self.raw_adc_data, start_index, end_index)


    # def stop_thread(self):
    #     self.worker
            



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()