import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget ,QSpinBox, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider
#from PyQt5.QtCore import Qt
from PyQt5 import QtCore
import h5py
import math_methods
from initial import initial_fields
from dragonradio.signal import decompressIQData
from spectrogram import spectrogram
from RF_view import RF_view
from traffic_view import Traffic_view
from linked_view import linked_view

class ui_components(QMainWindow,initial_fields):
    def __init__(self):
        super().__init__()

    def set_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #07294D; color: #FFC600;") #works like css stylesheets


    def tab_container(self):
        self.horizonal_layout = QHBoxLayout()

        #For graph type tabs        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("background-color: white; color: black;")

        self.horizonal_layout.addWidget(self.tabs)
        self.layout.addLayout(self.horizonal_layout)

    def loading_button(self):
        self.load_button = QPushButton("Load Log File")
        self.load_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_button.clicked.connect(self.load_file_all)
        self.layout.addWidget(self.load_button)

    def load_traffic_log_button(self):
        self.load_traffic = QPushButton("Load traffic logs")
        self.load_traffic.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_traffic.clicked.connect(self.load_traffic_file)
        self.layout.addWidget(self.load_traffic)
    

    def time_stretcher_setup(self):
        self.slider_val = 1
        time_slider_box = QVBoxLayout()
        self.time_slider = QSlider(QtCore.Qt.Horizontal)
        #sets initial slider settings
        self.time_slider.setMinimum(1)
        self.time_slider.setMaximum(50)
        self.time_slider.setValue(self.slider_val)
        self.time_slider.setTickPosition(QSlider.TicksBothSides)
        self.time_slider.setTickInterval(10)
        #calls function to update
        self.time_slider.valueChanged.connect(self.time_stretcher_update)
        time_slider_box.addWidget(self.time_slider)
        self.layout.addLayout(time_slider_box)

    def time_stretcher_update(self):
        self.slider_val = self.time_slider.value()
        plot_ref=self.ob_plot
        plot_ref.setXRange(self.current_x_range[1]-(1/self.slider_val),self.current_x_range[1],padding=0)
        plot_ref2=self.spectrogram
        plot_ref2.setXRange(self.current_x_range[1]-(1/self.slider_val),self.current_x_range[1],padding=0)
        #plot_ref3=self.setup_linked_traffic
        #plot_ref3.setXRange(self.current_x_range[1]-(1/self.slider_val),self.current_x_range[1],padding=0)

    def time_progress_slider_setup(self):
        time_progress_box = QVBoxLayout()
        self.time_progress = QSlider(QtCore.Qt.Horizontal)
        self.time_progress.setMinimum(0)
        self.time_progress.setMaximum(1)
        self.time_progress.setValue(0)
        self.time_progress.valueChanged.connect(self.time_progress_slider_update)
        time_progress_box.addWidget(self.time_progress)
        self.layout.addLayout(time_progress_box)

    def time_progress_slider_update(self):
        self.time_val = self.current_x_range[0]
        #print("test",self.time_progress.value(),int(self.time_val),self.current_x_range)
        plot_ref=self.ob_plot
        plot_ref.setXRange(self.time_val,self.time_val+self.time_step,padding=0)

    def setup_threshold_incrementor(self):
        self.dB_incrementer = QVBoxLayout()
        self.dB_spin_box = QSpinBox(self)
        self.dB_spin_box.setRange(-100, 100)
        self.dB_spin_box.setSuffix(" dB")
        self.dB_spin_box.valueChanged.connect(self.set_threshold_to_spinbox_value)
        self.dB_incrementer.addWidget(self.dB_spin_box)

    def set_threshold_to_spinbox_value(self):
        self.threshold = self.dB_spin_box.value()


    def load_file_all(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File","","HDF5 files (*.h5 *.hdf5);;MGEN files (*.drc)")
        self.index = 0
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        if file_path:
            if(file_path.endswith('.drc')):
                self.traffic_from_file(file_path)
                #self.linked_traffic_from_file(file_path)
            else:
                try:
                    #with h5py.File(file_path, 'r') as f:
                    f = h5py.File(file_path, 'r') 
                    key = 'snapshots'
                    self.max_index = int(len(f[key]["iq_data"]))
                    self.timer.timeout.connect(lambda: self.timed_plotting(f))
                    self.timer.start()
                except Exception as e:
                    print(f"Error loading or plotting file: {e}")

    def timed_plotting(self,f):
        if(self.index < self.max_index):
            self.plot_all_data_from_file(f,self.index)
            self.index+=1
        else:
            self.timer.stop()

    def load_traffic_file(self):
        file_path= QFileDialog.getExistingDirectory(None, "Select Folder", "")
        self.index = 0
        if file_path:
            self.traffic_logs_from_file(file_path)
            #self.traffic_logs_from_file_linked(file_path)
    
    def plot_all_data_from_file(self, file,index):
        timestamps = file['snapshots']['timestamp']
        data = file['snapshots']["iq_data"][index]
        fs = file['snapshots']["fs"][index]
        f,time_bins,Sxx_db = math_methods.calculate_spectrogram(decompressIQData(data),fs)
        self.plot_all_spectrogram(f,time_bins,Sxx_db,timestamps)
        self.append_data_binary_occupany(f,time_bins,Sxx_db,timestamps)

    
