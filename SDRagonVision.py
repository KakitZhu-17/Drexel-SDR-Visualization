import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget,QApplication,QSpinBox, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSlider
from PyQt5.QtCore import Qt
import h5py
import pyqtgraph as pg
import numpy as np
import spectrogram_setup
from dragonradio.signal import decompressIQData

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDRagon Vision")

        #===============useful fields for processing==========================
        self.index = 0
        self.max_index = None
        self.current_file_path = None
        self.global_time = 0
        self.global_time_step=0
        self.bin_factor = 6
        self.colormap_scheme = "viridis"
        self.threshold = -20
        self.slider_val = 1
        self.current_x_range = [0,0]

        #===============actual layout stuff===================================
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #07294D; color: #FFC600;") #works like css stylesheets

        self.load_button = QPushButton("Load Log File")
        self.load_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)

        self.horizonal_layout = QHBoxLayout()

        #For graph type tabs        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("background-color: white; color: black;")

        self.horizonal_layout.addWidget(self.tabs)
        self.layout.addLayout(self.horizonal_layout)

        self.setup_RF_View_tab()
        self.setup_spectrogram_tab()


        #threhold adjuster
        self.setup_threshold_incrmentor()

        self.horizonal_layout = QHBoxLayout()
        self.horizonal_layout.addLayout(self.dB_incrementer)

        self.horizonal_layout.addWidget(self.tabs)
        self.layout.addLayout(self.horizonal_layout)

        time_slider_box = QVBoxLayout()
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(1)
        self.time_slider.setMaximum(50)
        self.time_slider.setValue(self.slider_val)
        self.time_slider.setTickPosition(QSlider.TicksBothSides)
        self.time_slider.setTickInterval(10)
        self.time_slider.valueChanged.connect(self.time_slider_update)
        time_slider_box.addWidget(self.time_slider)
        self.layout.addLayout(time_slider_box)

        #Index control buttons
        index_control_layout = QHBoxLayout() #this is a horizontal layout box, it puts widget right next to each other


        self.next_button = QPushButton("next index",self)
        self.next_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.next_button.clicked.connect(self.next_button_click)

        self.index_count = QLabel("1",self)
        self.index_count.setAlignment(Qt.AlignCenter)

        self.prev_button = QPushButton("prev index",self)
        self.prev_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.prev_button.clicked.connect(self.prev_button_click)

        index_control_layout.addWidget(self.prev_button)
        index_control_layout.addWidget(self.index_count)
        index_control_layout.addWidget(self.next_button)

        self.layout.addLayout(index_control_layout)

    def time_slider_update(self):
        self.slider_val = self.time_slider.value()
        plot_ref=self.ob_plot
        plot_ref.setXRange(self.current_x_range[1]-(1/self.slider_val),self.current_x_range[1],padding=0)

    def setup_threshold_incrmentor(self):
        self.dB_incrementer = QVBoxLayout()
        self.dB_spin_box = QSpinBox(self)
        self.dB_spin_box.setRange(-100, 100)
        self.dB_spin_box.setSuffix(" dB")
        self.dB_spin_box.valueChanged.connect(self.set_threshold_to_spinbox_value)
        self.dB_incrementer.addWidget(self.dB_spin_box)

    def set_threshold_to_spinbox_value(self):
        self.threshold = self.dB_spin_box.value()
    
    def setup_RF_View_tab(self):
        #this is basically how you add a widget
        tab = QWidget()
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout() #this is a vertical layout box, it puts widgets on top of each other
        layout.addWidget(self.binary_occupany_layout)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "RF view")

    def setup_spectrogram_tab(self):
        tab = QWidget()
        self.setup_spectrogram = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout()
        layout.addWidget(self.setup_spectrogram)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "spectrogram")

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File","","(*)") #filters out files for h5 files
        self.index = 0
        if file_path:
            self.current_file_path = file_path
            self.plot_data_from_file(file_path)

    def update_view_range(self):
        #print(self.ob_plot.viewRange()[0])
        self.current_x_range = self.ob_plot.viewRange()[0]
            

    def binary_occupancy_from_data(self,f,time_bins,Sxx_db):
        self.binary_occupany_layout.clear()
        self.ob_plot = self.binary_occupany_layout.addPlot(title="RF View")

        freq_bin_factor = self.bin_factor

        F = len(f)
        T = len(time_bins)
        F_trim = (F // freq_bin_factor) * freq_bin_factor #this makes sure the frequency bins are divisible by bin factor
        f_trim = f[:F_trim]
        S_trim = Sxx_db[:F_trim,:T]     

        f_coarse = f_trim.reshape(len(f_trim)//freq_bin_factor, freq_bin_factor).mean(axis=1) 
        S_coarse = S_trim.reshape(len(f_coarse), freq_bin_factor, T).max(axis=1) #so basically it would reshape the spectrogram to len(f_coarse) number of bins, each bin is shaped(freq_bin_factor,T)

        threshold = np.mean(S_coarse)
        #print(float(threshold))
        self.dB_spin_box.setValue(int(threshold))
        threshold = self.threshold
        occupancy = (S_coarse > threshold).astype(float)
        
        plot = self.ob_plot
        img = pg.ImageItem()
        plot.addItem(img)
        img.setColorMap("magma")
        img.setImage(occupancy.T)
        plot.setLabel("left", "Frequency (kHz)")
        plot.setLabel("bottom", "Time (s)")
        freq_total = (f[-1] - f[0])

        img.setRect(pg.QtCore.QRectF(
            time_bins[0],
            f[0]/1e3,
            time_bins[-1],
            freq_total/1e3
        ))
                        
        self.binary_occupany_layout.addItem(plot)
        viewbox_call=plot.getViewBox()
        viewbox_call.setLimits(xMin=0,xMax=self.global_time+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
        viewbox_call.sigRangeChanged.connect(self.update_view_range)
    
    def append_data_binary_occupany(self,f,time_bins,Sxx_db):
        plot = self.ob_plot

        freq_bin_factor = self.bin_factor
        
        F = len(f)
        T = len(time_bins)

        F_trim = (F // freq_bin_factor) * freq_bin_factor
        f_trim = f[:F_trim]
        S_trim = Sxx_db[:F_trim, :T]

        f_coarse = f_trim.reshape(len(f_trim)//freq_bin_factor, freq_bin_factor).mean(axis=1)
        S_coarse = S_trim.reshape(len(f_coarse), freq_bin_factor, T).max(axis=1)

        threshold = self.threshold
        occupancy = (S_coarse > threshold).astype(float)

        img = pg.ImageItem()
        img.setColorMap("magma")
        img.setImage(occupancy.T)

        start_time = self.global_time    

        freq_step = (f[-1] - f[0])

        img.setRect(pg.QtCore.QRectF(
            start_time,
            f[0]/1e3,
            time_bins[-1],                                
            freq_step/ 1e3
        ))

        plot.addItem(img)
        viewbox_call=plot.getViewBox()
        viewbox_call.setLimits(xMin=0,xMax=self.global_time+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
        plot.setXRange(self.global_time, self.global_time+time_bins[-1],padding=0)
        self.global_time_step = time_bins[-1]


    def spectrogram_from_data(self,f,time_bins,Sxx_db):
        
        self.setup_spectrogram.clear()
        self.spectrogram = self.setup_spectrogram.addPlot(title="Spectrogram")
        
        plot = self.spectrogram
        plot.setLabel("left", "Frequency (kHz)")
        plot.setLabel("bottom", "Time (s)")

        img = pg.ImageItem()
        plot.addItem(img)
        cmap = pg.colormap.get(self.colormap_scheme)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        img.setLookupTable(lut)
        img.setImage(Sxx_db.T)
        
        freq_step = (f[-1] - f[0])

        colorbar = pg.ColorBarItem(
            values=(Sxx_db.min(), Sxx_db.max()), 
            colorMap= cmap,
            label="Power (dB)"
        )

        colorbar.setImageItem(img)

        img.setRect(pg.QtCore.QRectF(
            time_bins[0],       
            f[0]/1e3,       
            time_bins[-1],   
            freq_step/1e3
        ))
             
        self.setup_spectrogram.addItem(plot)
        self.setup_spectrogram.addItem(colorbar)

    def next_button_click(self):
        #print(self.index)
        if(self.index < self.max_index-1):
            self.index+=1
            self.plot_data_from_file(self.current_file_path)
            self.index_count.setText(str(self.index))
            self.slider_val = 1
            self.time_slider.setValue(1)
    
    def prev_button_click(self):
        #print(self.index)
        if(self.index >= 0):
            self.index-=1
            self.plot_data_from_file(self.current_file_path)
            self.index_count.setText(str(self.index))

    def plot_data_from_file(self, file_path):
        try:
            with h5py.File(file_path, 'r') as f:
                key = 'snapshots'
                data = f[key]["iq_data"][self.index]
                fs = f[key]["fs"][self.index]
                self.max_index = len(f[key]["iq_data"])
                if(data.dtype == "int8"):
                    f,time_bins,Sxx_db = spectrogram_setup.calculate_spectrogram(decompressIQData(data),fs)
                
                    if(self.index == 0): #checks if its loading a new file
                        self.binary_occupancy_from_data(f,time_bins,Sxx_db)
                        self.spectrogram_from_data(f,time_bins,Sxx_db)
                    else:
                        self.append_data_binary_occupany(f,time_bins,Sxx_db)
                        self.spectrogram_from_data(f,time_bins,Sxx_db)
                    self.global_time += time_bins[-1]

                elif(data.dtype == "complex64"):
                    f,time_bins,Sxx_db = spectrogram_setup.calculate_spectrogram(data,fs)
                    if(self.index == 0):
                        self.binary_occupancy_from_data(f,time_bins,Sxx_db)
                        self.spectrogram_from_data(f,time_bins,Sxx_db)
                    else:
                        self.append_data_binary_occupany(f,time_bins,Sxx_db)
                        self.spectrogram_from_data(f,time_bins,Sxx_db)
                    self.global_time += time_bins[-1]
                
                else:
                    print(f[key]["iq_data"][self.index].dtype)

        except Exception as e:
            print(f"Error loading or plotting file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())