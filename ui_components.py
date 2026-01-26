import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget ,QSpinBox, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider
from PyQt5 import QtCore
import pyqtgraph as pg
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
        self.slot_arr=[]

    def set_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #07294D; color: #FFC600;") #works like css stylesheets


    def tab_container(self):
        self.vertical_layout = QVBoxLayout()
        #For graph type tabs        
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setStyleSheet("background-color: white; color: black;")
        self.vertical_layout.addWidget(self.tabs)
        self.layout.addLayout(self.vertical_layout)

    def loading_button(self):
        self.load_button = QPushButton("Load Log File")
        self.load_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)


    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File","","HDF5 files (*.h5 *.hdf5);;MGEN files (*.drc)")
        self.index = 0
        timer = QtCore.QTimer(self)
        timer.setInterval(500)
        if file_path:
            if(file_path.endswith('.drc')):
                self.traffic_from_file(file_path)
            else:
                try:
                    f = h5py.File(file_path, 'r') 
                    key = 'snapshots'
                    self.max_index = int(len(f[key]["iq_data"]))
                    timer.timeout.connect(lambda: self.slot_arr[0].timed_plotting(f,self.max_index,timer))
                    timer.start()
                except Exception as e:
                    print(f"Error loading or plotting file: {e}")


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

    def setup_threshold_incrementor(self):
        self.dB_incrementer = QVBoxLayout()
        self.dB_spin_box = QSpinBox(self)
        self.dB_spin_box.setRange(-100, 100)
        self.dB_spin_box.setSuffix(" dB")
        self.dB_spin_box.valueChanged.connect(self.set_threshold_to_spinbox_value)
        self.dB_incrementer.addWidget(self.dB_spin_box)

    def set_threshold_to_spinbox_value(self):
        self.threshold = self.dB_spin_box.value()


    #def timed_plotting(self,f):
    #    if(self.index < self.max_index):
    #        self.plot_all_data_from_file(f,self.index)
    #        self.index+=1
    #    else:
    #        self.timer.stop()

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

class file_slot(spectrogram,RF_view):
    def __init__(self):
        super().__init__()
        self.spectrogram_ref = None
        self.RF_ref = None
        self.index = 0

    def slot_setup(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        graph_tabs = QTabWidget()
        layout.addWidget(graph_tabs)


        plot_tabs = QWidget()
        self.spectrogram_ref= spectrogram()
        spectrogram_tab= self.spectrogram_ref.spectrogram_tab_setup()
        spectrogram_layout = QVBoxLayout()
        spectrogram_layout.addWidget(spectrogram_tab)
        plot_tabs.setLayout(spectrogram_layout)
        graph_tabs.addTab(plot_tabs, "Spectrogram")

        plot_tabs2 = QWidget()
        self.RF_ref= RF_view()
        RF_tab= self.RF_ref.RF_view_tab_setup()
        RF_layout = QVBoxLayout()
        RF_layout.addWidget(RF_tab)
        plot_tabs2.setLayout(RF_layout)
        graph_tabs.addTab(plot_tabs2, "RF_view")


        return tab

    def timed_plotting(self,f,max_index,timer):
        if(self.index < max_index):
            self.plot_all_data_from_file(f,max_index)
            self.index+=1
        else:
            timer.stop()

    def plot_all_data_from_file(self,file,max_index):
        timestamps = file['snapshots']['timestamp']
        data = file['snapshots']["iq_data"][self.index]
        fs = file['snapshots']["fs"][self.index]
        f,time_bins,Sxx_db = math_methods.calculate_spectrogram(decompressIQData(data),fs)
        self.spectrogram_ref.max_index = max_index
        self.spectrogram_ref.index = self.index
        self.spectrogram_ref.plot_all_spectrogram(f,time_bins,Sxx_db,timestamps)
        self.RF_ref.max_index = max_index
        self.RF_ref.index = self.index
        self.RF_ref.append_data_binary_occupany(f,time_bins,Sxx_db,timestamps)


    
