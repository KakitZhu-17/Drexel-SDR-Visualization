import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget ,QSpinBox, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider
from PyQt5.QtCore import Qt
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
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)
    
    def index_controls(self):
        index_control_layout = QHBoxLayout() #this is a horizontal layout box, it puts widget right next to each other


        self.next_button = QPushButton("next index",self)
        self.next_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.next_button.clicked.connect(self.next_button_click)

        self.index_count = QLabel(str(self.index),self)
        self.index_count.setAlignment(Qt.AlignCenter)

        self.prev_button = QPushButton("prev index",self)
        self.prev_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.prev_button.clicked.connect(self.prev_button_click)

        index_control_layout.addWidget(self.prev_button)
        index_control_layout.addWidget(self.index_count)
        index_control_layout.addWidget(self.next_button)

        self.layout.addLayout(index_control_layout)

    def time_stretcher_setup(self):
        self.slider_val = 1
        time_slider_box = QVBoxLayout()
        self.time_slider = QSlider(Qt.Horizontal)
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
        plot_ref2=self.linked_ob_plot
        plot_ref2.setXRange(self.current_x_range[1]-(1/self.slider_val),self.current_x_range[1],padding=0)
        plot_ref3=self.setup_linked_traffic
        plot_ref3.setXRange(self.current_x_range[1]-(1/self.slider_val),self.current_x_range[1],padding=0)

    def time_progress_slider_setup(self):
        time_progress_box = QVBoxLayout()
        self.time_progress = QSlider(Qt.Horizontal)
        self.time_progress.setMinimum(0)
        self.time_progress.setMaximum(1)
        self.time_progress.setValue(0)
        #self.time_progress.setTickPosition(QSlider.TicksBothSides)
        #self.time_progress.setTickInterval(10)
        self.time_progress.valueChanged.connect(self.time_progress_slider_update)
        time_progress_box.addWidget(self.time_progress)
        self.layout.addLayout(time_progress_box)

    def time_progress_slider_update(self):
        self.time_val = self.current_x_range[0]
        print("test",self.time_progress.value(),int(self.time_val),self.current_x_range)
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


    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File","","HDF5 files (*.h5 *.hdf5);;MGEN files (*.drc)")
        self.index = 0
        if file_path:
            if(file_path.endswith('.drc')):
                self.traffic_from_file(file_path)
                self.linked_traffic_from_file(file_path)
            else:
                self.current_file_path = file_path
                self.plot_data_from_file(file_path)

    def update_view_range(self):
        self.current_x_range = self.ob_plot.viewRange()[0]
            

    def next_button_click(self):
        if(self.index < self.max_index-1):
            #print(self.ob_plot.viewRange()[0][0])
            self.index+=1
            self.plot_data_from_file(self.current_file_path)
            self.index_count.setText(str(self.index))
            self.slider_val = 1
            self.time_slider.setValue(1)
    
    def prev_button_click(self):
        if(self.index >= 0):
            self.index-=1
            self.plot_data_from_file(self.current_file_path,True)
            self.index_count.setText(str(self.index))

    def plot_data_from_file(self, file_path, prev = False):
        try:
            with h5py.File(file_path, 'r') as f:
                key = 'snapshots'
                #print(f.keys())
                data = f[key]["iq_data"][self.index]
                fs = f[key]["fs"][self.index]
                timestamps = f['snapshots']['timestamp']
                self.max_index = len(f[key]["iq_data"])
                if(data.dtype == "int8"):
                    f,time_bins,Sxx_db = math_methods.calculate_spectrogram(decompressIQData(data),fs)
                    self.time_step = time_bins[-1]
                
                    if(self.index == 0): #checks if its loading a new file
                        self.binary_occupancy_from_file(f,time_bins,Sxx_db,timestamps)
                        self.spectrogram_from_file(f,time_bins,Sxx_db,timestamps)
                        self.linked_binary_occupancy_from_file(f,time_bins,Sxx_db,timestamps)
                    elif(not prev):
                        self.append_data_binary_occupany(f,time_bins,Sxx_db)
                        self.spectrogram_from_file(f,time_bins,Sxx_db,timestamps)
                        self.linked_append_data_binary_occupany(f,time_bins,Sxx_db)
                    else:
                        self.spectrogram_from_file(f,time_bins,Sxx_db,timestamps)
                    if(self.index+1 < self.max_index):
                        self.global_time = timestamps[self.index+1]

                elif(data.dtype == "complex64"):
                    f,time_bins,Sxx_db = math_methods.calculate_spectrogram(data,fs)
                    if(self.index == 0): #checks if its loading a new file
                        self.binary_occupancy_from_file(f,time_bins,Sxx_db,timestamps)
                        self.spectrogram_from_file(f,time_bins,Sxx_db,timestamps)
                    elif(not prev):
                        self.append_data_binary_occupany(f,time_bins,Sxx_db)
                        self.spectrogram_from_file(f,time_bins,Sxx_db,timestamps)
                    else:
                        self.spectrogram_from_file(f,time_bins,Sxx_db,timestamps)
                    if(self.index+1 < self.max_index):
                        self.global_time = timestamps[self.index+1]
                
                else:
                    print(f[key]["iq_data"][self.index].dtype)

        except Exception as e:
            print(f"Error loading or plotting file: {e}")
