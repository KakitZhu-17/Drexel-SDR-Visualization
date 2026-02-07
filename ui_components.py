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
from acc_view import all_view

class ui_components(QMainWindow,initial_fields):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setStyleSheet("background-color: white; color: black;")

        self.accumulated_tab = all_view()
        self.accumulated_slot = self.accumulated_tab.all_view_tab_setup()
        self.tabs.addTab(self.accumulated_slot, "all")

        self.slot_arr=[]
        self.file_arr=[]
        self.max_time=0

        self.traffic_log=None

    def set_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #07294D; color: #FFC600;") #works like css stylesheets


    def tab_container(self):
        self.vertical_layout = QVBoxLayout()
        #For graph type tabs        
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
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        if file_path:
            if(file_path.endswith('.drc')):
                #self.traffic_from_file(file_path)
                if(len(self.slot_arr)>0):
                    for slot in self.slot_arr:
                        slot.traffic_ref.traffic_from_file(file_path)
            else:
                try:
                    f = h5py.File(file_path, 'r') 
                    self.file_arr.append(f)
                    self.add_slot(str(len(self.slot_arr)+1))
                    current_slot_index=len(self.slot_arr)-1
                    key = 'snapshots'
                    max_index = int(len(f[key]["iq_data"]))
                    current_max = int(f[key]['timestamp'][-1]+1.55) 
                    if(current_max > self.max_time):
                        self.time_progress.setMaximum(current_max)

                    if(self.traffic_log != None):
                        self.slot_arr[-1].traffic_ref.traffic_logs_from_file(self.traffic_log)


                    print(file_path)
                    self.timer.timeout.connect(lambda: self.timed_plotting(self.slot_arr[current_slot_index],f,max_index,current_slot_index))
                    self.timer.start()
                except Exception as e:
                    print(f"Error loading or plotting file: {e}")

    def add_slot(self,slot_name):
        fileslot = file_slot()
        setup_file_slot = fileslot.slot_setup()
        self.tabs.addTab(setup_file_slot, slot_name)
        self.slot_arr.append(fileslot)

    def timed_plotting(self,slot_ref,f,max_index,current_slot_index):
        if(self.index < max_index):
            slot_ref.plot_all_data_from_file(f,self.index,max_index,current_slot_index)
            self.accumulated_tab.plot_all_data_from_file(f,self.index,max_index,current_slot_index)
            self.index+=1
        else:
            self.timer.stop()

    def load_traffic_log_button(self):
        self.load_traffic = QPushButton("Load traffic logs")
        self.load_traffic.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_traffic.clicked.connect(self.load_traffic_file)
        self.layout.addWidget(self.load_traffic)

    def update_view_range(self):
        self.current_x_range =  self.accumulated_tab.RF_ref.RF_widget.viewRange()[0]

    def time_stretcher_setup(self):
        time_slider_box = QVBoxLayout()
        self.time_slider = QSlider(QtCore.Qt.Horizontal)
        #sets initial slider settings
        self.time_slider.setRange(1, 9)
        self.time_slider.setValue(1)
        self.time_slider.setTickPosition(QSlider.TicksBothSides)
        self.time_slider.setTickInterval(1)
        #calls function to update
        self.time_slider.valueChanged.connect(self.time_stretcher_update)
        time_slider_box.addWidget(self.time_slider)
        self.layout.addLayout(time_slider_box)

    def time_stretcher_update(self):
        current_start = self.time_progress.value()
        current_end = self.time_progress.value()+1.5
        test = (1.5)* (self.time_slider.value()/10)
        zoom= (self.time_progress.value()+1.5)-test
        for slot in self.slot_arr:
            slot.spectrogram_ref.spectrogram_widget.setXRange(current_start,zoom,padding=0)
            slot.traffic_ref.update_traffic_view_range(current_start,zoom)
        self.accumulated_tab.RF_widget.setXRange(current_start,zoom,padding=0)

    def time_progress_slider_setup(self):
        time_progress_box = QVBoxLayout()
        self.time_progress = QSlider(QtCore.Qt.Horizontal)
        self.time_progress.setMinimum(0)
        self.time_progress.setMaximum(10)
        self.time_progress.setValue(0)
        self.time_progress.valueChanged.connect(self.time_progress_slider_update)
        time_progress_box.addWidget(self.time_progress)
        self.layout.addLayout(time_progress_box)

    def time_progress_slider_update(self):
        #self.accumulated_tab.RF_ref.RF_widget.setXRange(self.time_progress.value(),self.time_progress.value()+1.5,padding=0)
        self.accumulated_tab.RF_widget.setXRange(self.time_progress.value(),self.time_progress.value()+1.5,padding=0)
        for slot in self.slot_arr:
            #slot.RF_ref.RF_widget.setXRange(self.time_progress.value(),self.time_progress.value()+1.5,padding=0)
            slot.spectrogram_ref.spectrogram_widget.setXRange(self.time_progress.value(),self.time_progress.value()+1.5,padding=0)
        self.time_stretcher_update()

    def setup_threshold_incrementor(self):
        self.dB_incrementer = QVBoxLayout()
        self.dB_spin_box = QSpinBox(self)
        self.dB_spin_box.setRange(-100, 100)
        self.dB_spin_box.setSuffix(" dB")
        self.dB_spin_box.valueChanged.connect(self.set_threshold_to_spinbox_value)
        self.dB_incrementer.addWidget(self.dB_spin_box)

    def set_threshold_to_spinbox_value(self):
        self.threshold = self.dB_spin_box.value()


    def load_traffic_file(self):
        self.traffic_log = QFileDialog.getExistingDirectory(None, "Select Folder", "")
        if self.traffic_log:
            if(len(self.slot_arr)>0):
                for slot in self.slot_arr:
                    slot.traffic_ref.traffic_logs_from_file(self.traffic_log)


class file_slot(spectrogram,RF_view):
    def __init__(self):
        super().__init__()
        self.spectrogram_ref = None
        self.RF_ref = None
        self.traffic_ref =None
        self.index = 0
        self.colors = [[255, 255, 0, 255],[0, 255, 0, 255],[0, 0, 255, 255],[0, 255, 255, 255]]

    def slot_setup(self,all_tab = False):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        graph_tabs = QTabWidget()
        layout.addWidget(graph_tabs)

        #ob_plot_tab = QWidget()
        #self.RF_ref= RF_view()
        #RF_tab= self.RF_ref.RF_view_tab_setup()
        #RF_layout = QVBoxLayout()
        #RF_layout.addWidget(RF_tab)
        #ob_plot_tab.setLayout(RF_layout)
        #graph_tabs.addTab(ob_plot_tab, "RF_view")

        if(all_tab == False):
            plot_tabs = QWidget()
            self.spectrogram_ref= spectrogram()
            spectrogram_tab= self.spectrogram_ref.spectrogram_tab_setup()
            spectrogram_layout = QVBoxLayout()
            spectrogram_layout.addWidget(spectrogram_tab)
            plot_tabs.setLayout(spectrogram_layout)
            graph_tabs.addTab(plot_tabs, "Spectrogram")

            traffic_plot_tabs = QWidget()
            self.traffic_ref= Traffic_view()
            traffic_tab= self.traffic_ref.traffic_tab_setup()
            traffic_layout = QVBoxLayout()
            traffic_layout.addWidget(traffic_tab)
            traffic_plot_tabs.setLayout(traffic_layout)

            self.spectrogram_ref2= spectrogram()
            self.spectrogram2_tab= self.spectrogram_ref2.spectrogram_tab_setup()
            self.traffic_ref.add_widget(self.spectrogram2_tab,self.spectrogram_ref2)

            graph_tabs.addTab(traffic_plot_tabs, "Traffic")

        return tab

    def plot_all_data_from_file(self,file,index,max_index,color_index):
        timestamps = file['snapshots']['timestamp']
        data = file['snapshots']["iq_data"][index]
        fs = file['snapshots']["fs"][index]
        f,time_bins,Sxx_db = math_methods.calculate_spectrogram(decompressIQData(data),fs)
        #print(timestamps[0]+time_bins[-1])
        
        if(self.spectrogram_ref != None):
            self.spectrogram_ref.max_index = max_index
            self.spectrogram_ref.index = index

            self.spectrogram_ref.append_spectrogram(f,time_bins,Sxx_db,timestamps)

            self.spectrogram_ref2.max_index = max_index
            self.spectrogram_ref2.index = index

            self.spectrogram_ref2.append_spectrogram(f,time_bins,Sxx_db,timestamps)

            #self.RF_ref.max_index = max_index
            #self.RF_ref.index = index
            #self.RF_ref.append_data_binary_occupany_test(f,time_bins,Sxx_db,timestamps,self.colors[color_index])

        #self.RF_ref.max_index = max_index
        #self.RF_ref.index = index
        #self.RF_ref.layer_append(f,time_bins,Sxx_db,timestamps,self.colors[color_index])



    
