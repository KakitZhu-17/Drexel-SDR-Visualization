import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget,QApplication, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
import h5py
import pyqtgraph as pg
import numpy as np
from scipy.signal import spectrogram, welch
from pyqtgraph.Qt import QtGui
import matplotlib.pyplot as plt

def calculate_spectrogram(data,sample_rate):
    f, time_bins, Sxx = spectrogram(
        data,
        fs=sample_rate,
        nperseg=512,
        noverlap=256,
        nfft=512,
        window="hann",
        return_onesided=False
    )

    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-12)
    Sxx_db = np.fft.fftshift(Sxx_db, axes=0)
    f = np.fft.fftshift(f)

    return f,time_bins,Sxx_db



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDRagon Vision")
        self.index = 0
        self.max_index = None
        self.current_file_path = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #07294D; color: #FFC600;") #works like css stylesheets

        self.load_button = QPushButton("Load Log File")
        self.load_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)

        #buttons for transmitter (for mock up only, delete later)
        self.transmitter_sources_widget = QVBoxLayout()
        transmitter_sources_names = QPushButton("transmitter1")
        transmitter_sources_names.setStyleSheet("background-color: #006699; color: #FFC600;")
        transmitter_sources_names2 = QPushButton("transmitter2")
        transmitter_sources_names2.setStyleSheet("background-color: #006699; color: #FFC600;")
        
        self.transmitter_sources_widget.addWidget(transmitter_sources_names)
        self.transmitter_sources_widget.addWidget(transmitter_sources_names2)

        self.horizonal_layout = QHBoxLayout()
        self.horizonal_layout.addLayout(self.transmitter_sources_widget)

        #For graph type tabs        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("background-color: white; color: black;")

        self.horizonal_layout.addWidget(self.tabs)
        self.layout.addLayout(self.horizonal_layout)

        self.setup_RF_View_tab()
        self.setup_spectrogram_tab()

        #Index control buttons
        index_control_layout = QHBoxLayout()

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
        
    def setup_line_graph_tab(self):
        #Creates the page (container widget) for the first tab
        tab = QWidget()

        self.plot_widget = pg.PlotWidget()
        
        #Creates a layout for this specific tab
        layout = QVBoxLayout()
        
        #Adds widgets to the layout
        layout.addWidget(self.plot_widget)
        
        #Set the layout on the container widget
        tab.setLayout(layout)
        
        #Adds the container widget to the main QTabWidget
        self.tabs.addTab(tab, "Line graph")
    
    def setup_RF_View_tab(self):
        tab = QWidget()
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout()
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
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Data File","","(*.h5)")
        self.index = 0
        if file_path:
            self.current_file_path = file_path
            self.plot_data_from_file(file_path)

    def line_graph(self,x,y):
        self.plot_widget.clear() # Clear previous plot
        self.plot_widget.plot(x, y, pen = 'b')
        self.plot_widget.setLabel('left', 'psd dB/Hz')
        self.plot_widget.setLabel('bottom', 'frequencies (Hz)')
    

    def binary_occupancy_from_data(self,data,sample_rate):

        self.binary_occupany_layout.clear()

        f,time_bins,Sxx_db = calculate_spectrogram(data,sample_rate)
        freq_bin_factor = 1          
        F = len(f)
        T = len(time_bins)
        F_trim = (F // freq_bin_factor) * freq_bin_factor
        f_trim = f[:F_trim]
        S_trim = Sxx_db[:F_trim,:T]     

        f_coarse = f_trim.reshape(-1, freq_bin_factor).mean(axis=1) 
        S_coarse = S_trim.reshape(len(f_coarse), freq_bin_factor, T).max(axis=1)  

        thr_offset_db = 0   # try 3,6,9,12
        threshold = np.median(S_coarse) + thr_offset_db
        print(threshold)
        occupancy = (S_coarse > threshold).astype(float)
        
        plot = self.binary_occupany_layout.addPlot(title="RF View")
        img = pg.ImageItem()
        plot.addItem(img)
        img.setColorMap("inferno")
        img.setImage(occupancy.T)
        plot.setLabel("left", "Frequency (kHz)")
        plot.setLabel("bottom", "Time (s)")

        time_step = time_bins[1] - time_bins[0]
        freq_step = (f[1] - f[0])

        img.setRect(pg.QtCore.QRectF(
            time_bins[0],       
            f[0]/1e3,       
            time_step * Sxx_db.shape[1],   
            freq_step/1e3 * Sxx_db.shape[0]
        ))
                        
        self.binary_occupany_layout.addItem(plot)


    def spectrogram_from_data(self,data,sample_rate):

        self.setup_spectrogram.clear()

        f,time_bins,Sxx_db = calculate_spectrogram(data,sample_rate)
        
        plot = self.setup_spectrogram.addPlot(title="Spectrogram")
        plot.setLabel("left", "Frequency (kHz)")
        plot.setLabel("bottom", "Time (s)")

        img = pg.ImageItem()
        plot.addItem(img)
        cmap = pg.colormap.get('viridis')
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        img.setLookupTable(lut)
        img.setLevels([Sxx_db.min(), Sxx_db.max()])
        img.setImage(Sxx_db.T)
        
        time_step = time_bins[1] - time_bins[0]
        freq_step = (f[1] - f[0])

        colorbar = pg.ColorBarItem(
            values=(Sxx_db.min(), Sxx_db.max()), 
            colorMap= cmap,
            label="Power (dB)"
        )

        colorbar.setImageItem(img)

        img.setRect(pg.QtCore.QRectF(
            time_bins[0],       
            f[0]/1e3,       
            time_step * Sxx_db.shape[1],   
            freq_step/1e3 * Sxx_db.shape[0]
        ))
             
        self.setup_spectrogram.addItem(plot)
        self.setup_spectrogram.addItem(colorbar)

    def next_button_click(self):
        print(self.index)
        if(self.index < self.max_index-1):
            self.index+=1
            self.plot_data_from_file(self.current_file_path)
            self.index_count.setText(str(self.index+1))
    
    def prev_button_click(self):
        print(self.index)
        if(self.index >= 0):
            self.index-=1
            self.plot_data_from_file(self.current_file_path)
            self.index_count.setText(str(self.index+1))

    def plot_data_from_file(self, file_path):
        try:
            with h5py.File(file_path, 'r') as f:
                key = 'snapshots'
                data = f[key]["iq_data"][self.index]
                fs = f['snapshots']["fs"][0]
                self.max_index = len(data)
                if(data.dtype == "int8"):
                    sample = data
                    if len(data) % 2 != 0:
                        sample = data[:-1]
                    iq_data = sample[::2] + 1j*sample[1::2]
                    iq_data = iq_data /128

                    #-------this is for debugging so ignore it-----------
                    #this is a simple signal/tone
                    #fs = 1e6   
                    #t = np.arange(1024*1000)/fs # time vector
                    #f = 50e3 # freq of tone
                    #x = np.sin(2*np.pi*f*t) + 0.2*np.random.randn(len(t))


                    #burst tone
                    #fs = 1e6
                    #t = np.arange(int(fs)) / fs
                    #f = 100e3
                    #burst = np.sin(2*np.pi*f*t)
                    #burst[:200000] = 0     
                    #burst[200000:400000] *= 1  
                    #burst[400000:] = 0     

                    self.binary_occupancy_from_data(data,fs)
                    self.spectrogram_from_data(data,fs)
                elif(data.dtype == "complex64"):
                    self.binary_occupancy_from_data(data,fs)
                    self.spectrogram_from_data(data,fs)
                else:
                    print(f[key]["iq_data"][self.index].dtype)
        except Exception as e:
            print(f"Error loading or plotting file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())