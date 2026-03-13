import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget ,QSpinBox, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider, QShortcut
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor,QKeySequence
from PyQt5 import QtCore
import pyqtgraph as pg
import numpy as np
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
        self.time_line = self.accumulated_tab.time_line
        self.time_line.sigPositionChanged.connect(self.update_time_line)

        self.slot_arr=[]
        self.file_arr=[]
        self.max_time=0
        self.max_traffic_power = None
        self.min_traffic_power = None
        self.current_x_start = 0
        self.current_x_end = 0
        self.traffic_log=None
        
        self.right_key = QShortcut(QKeySequence("D"), self)
        self.right_key.activated.connect(self.right_scroll)

        self.left_key = QShortcut(QKeySequence("A"), self)
        self.left_key.activated.connect(self.left_scroll)


    def set_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #07294D; color: #FFC600;") #works like css stylesheets

    def play_button_setup(self):
        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        
        self.play = False
        self.timer2 = QtCore.QTimer(self)
        self.timer2.setInterval(100)
        self.timer2.timeout.connect(self.right_scroll)

        self.play_button.clicked.connect(self.update_play_button)
        self.layout.addWidget(self.play_button)

    def update_play_button(self):
        if(self.play == True):
            self.timer2.stop()
            self.play = False
            self.play_button.setText("Play")
        elif(self.play == False):
            self.timer2.start()
            self.play = True
            self.play_button.setText("Stop")


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
        self.timer.setInterval(10)
        if file_path:
            if(file_path.endswith('.drc')):
                if(len(self.slot_arr)>0):
                    for slot in self.slot_arr:
                        slot.traffic_ref.traffic_from_file(file_path)
            else:
                try:
                    f = h5py.File(file_path, 'r') 
                    self.file_arr.append(f)
                    self.node_id = f.attrs['node_id']
                    self.add_slot()
                    current_slot_index=len(self.slot_arr)-1
                    key = 'snapshots'
                    #print(f.keys())
                    #print(f["tx_records"].dtype)
                    #print(f.attrs.keys())
                    print(f.attrs['node_id'])
                    max_index = int(len(f[key]["iq_data"]))
                    current_max = (int(f[key]['timestamp'][-1]+1.55))
                    fs = f['snapshots']["fs"][0]
                    data = f[key]["iq_data"]
                    timestamps = f['snapshots']['timestamp']

                    if(current_max > self.max_time):
                        self.time_progress.setMaximum(current_max)
                        self.max_time = current_max

                    if(self.traffic_log != None):
                        self.slot_arr[-1].traffic_ref.traffic_logs_from_file(self.traffic_log)

                    self.slot_arr[current_slot_index].traffic_ref.traffic_from_h5_file(f)

                    print(file_path)
                    self.timer.timeout.connect(lambda: self.timed_plotting(self.slot_arr[current_slot_index],data,fs,timestamps,max_index,current_slot_index))
                    self.timer.start()
                except Exception as e:
                    print(f"Error loading or plotting file: {e}")
        
    def add_slot(self):
        fileslot = file_slot()
        tab_name = "Node-" + str(self.node_id)
        setup_file_slot = fileslot.slot_setup()
        self.tabs.addTab(setup_file_slot, tab_name)
        self.slot_arr.append(fileslot)

    def timed_plotting(self,slot_ref,data,fs,timestamps,max_index,current_slot_index):
        if(self.index < max_index):
            f,time_bins,Sxx_db = math_methods.calculate_spectrogram(decompressIQData(data[self.index]),fs)
            
            slot_ref.plot_all_data_from_file(f,time_bins,Sxx_db,timestamps,self.index,max_index,current_slot_index)
            self.accumulated_tab.plot_all_data_from_file(f,time_bins,Sxx_db,timestamps,self.index,max_index,current_slot_index,self.node_id)
            
            self.index+=1
        else:
            print("done")
            self.timer.stop()

    def load_traffic_log_button(self):
        self.load_traffic = QPushButton("Load traffic logs")
        self.load_traffic.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_traffic.clicked.connect(self.load_traffic_file)
        self.layout.addWidget(self.load_traffic)

    def update_view_range(self):
        self.current_x_range =  self.accumulated_tab.RF_ref.RF_widget.viewRange()[0]

    def right_scroll(self):
        self.current_x_start+=0.025
        self.current_x_end+=0.025
        self.left_bound = self.time_line.value() - self.accumulated_tab.RF_widget.viewRange()[0][0]
        self.accumulated_tab.RF_widget.setXRange(self.current_x_start,self.current_x_end,padding=0)
        self.time_line.setPos(self.current_x_start+self.left_bound)

    def left_scroll(self):
        if(self.current_x_start > 0):
            self.current_x_start-=0.025
            self.current_x_end-=0.025
            self.left_bound = self.time_line.value() - self.accumulated_tab.RF_widget.viewRange()[0][0]
            self.accumulated_tab.RF_widget.setXRange(self.current_x_start,self.current_x_end,padding=0)
            self.time_line.setPos(self.current_x_start+self.left_bound)
        

    def update_time_line(self):
        slot_index = 0
        self.right_bound = self.accumulated_tab.RF_widget.viewRange()[0][1] - self.time_line.value()
        self.left_bound = self.time_line.value() - self.accumulated_tab.RF_widget.viewRange()[0][0]
        
        for slot in self.slot_arr:
            slot.spectrogram_ref.spectrogram_widget.setXRange(self.current_x_start,self.current_x_end,padding=0)
            slot.traffic_ref.update_traffic_view_range(self.current_x_start,self.current_x_end)
            slot.traffic_ref.update_time_line(self.accumulated_tab.time_line.value())

            if(len(slot.traffic_ref.plot_time_data) > 0):
                if(self.accumulated_tab.time_line.value() <= slot.traffic_ref.plot_time_data[-1]):
                    interpolated_data = np.interp(self.accumulated_tab.time_line.value(), slot.traffic_ref.plot_time_data, slot.traffic_ref.plot_size_data)
                else:
                    interpolated_data = 0
                self.accumulated_tab.update_progressbar_value(slot_index,interpolated_data*100)
            else:
                self.accumulated_tab.update_progressbar_value(slot_index,0)
            slot_index+=1

        self.current_x_start = self.accumulated_tab.RF_widget.viewRange()[0][0]
        self.current_x_end = self.accumulated_tab.RF_widget.viewRange()[0][1]
        
        if(self.accumulated_tab.RF_widget.viewRange()[0][0] >= int(self.accumulated_tab.RF_widget.viewRange()[0][0])):
            self.time_progress.setValue(self.accumulated_tab.RF_widget.viewRange()[0][0])
        

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
        self.current_start = self.time_progress.value()
        
        shrink = (1.5)* (self.time_slider.value()/10)
        zoom=(self.current_start+1.5)-shrink

        self.current_end = zoom
        
        self.left_bound = self.time_line.value() - self.accumulated_tab.RF_widget.viewRange()[0][0]
        self.accumulated_tab.RF_widget.setXRange(self.current_start,zoom,padding=0)
        self.time_line.setPos((self.accumulated_tab.RF_widget.viewRange()[0][0]+self.accumulated_tab.RF_widget.viewRange()[0][1])/2)
        
        for slot in self.slot_arr:
            slot.spectrogram_ref.spectrogram_widget.setXRange(self.current_start,zoom,padding=0)
            slot.traffic_ref.update_traffic_view_range(self.current_start ,zoom)
        

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
        current_time = self.time_progress.value()
        self.accumulated_tab.RF_widget.setXRange(current_time,current_time + 1,padding=0)
        self.left_bound = self.time_line.value() - self.current_x_start
        self.accumulated_tab.time_line.setPos(current_time+self.left_bound)

        slot_index = 0
        for slot in self.slot_arr:
            slot.spectrogram_ref.spectrogram_widget.setXRange(current_time,current_time+1,padding=0)
            slot.traffic_ref.update_traffic_view_range(current_time,current_time+1)
            slot.traffic_ref.update_time_line(self.accumulated_tab.time_line.value())
            
            if(len(slot.traffic_ref.plot_time_data) > 0):
                if(self.accumulated_tab.time_line.value() <= slot.traffic_ref.plot_time_data[-1]):
                    interpolated_data = np.interp(self.accumulated_tab.time_line.value(), slot.traffic_ref.plot_time_data, slot.traffic_ref.plot_size_data)
                else:
                    interpolated_data = 0
                self.accumulated_tab.update_progressbar_value(slot_index,interpolated_data*100)
            else:
                self.accumulated_tab.update_progressbar_value(slot_index,0)

            slot_index+=1

        self.current_x_start = current_time
        self.current_x_end = current_time + 1

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

    def plot_all_data_from_file(self,f,time_bins,Sxx_db,timestamps,index,max_index,color_index):
        
        self.spectrogram_ref.max_index = max_index
        self.spectrogram_ref.index = index

        self.spectrogram_ref.append_spectrogram(f,time_bins,Sxx_db,timestamps)

        self.spectrogram_ref2.max_index = max_index
        self.spectrogram_ref2.index = index

        self.spectrogram_ref2.append_spectrogram(f,time_bins,Sxx_db,timestamps)

    
