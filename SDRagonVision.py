import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget,QApplication, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
import h5py
import pyqtgraph as pg
import numpy as np
from scipy.signal import spectrogram, welch
from pyqtgraph.Qt import QtGui

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

        #self.setup_line_graph_tab()
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
    
    def setup_spectrogram_tab(self):
        tab = QWidget()
        self.spectrogram_layout = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout()
        layout.addWidget(self.spectrogram_layout)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Spectrogram")

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
    

    def psdAndFreq(self,data):
    
        Fs = 147794 / 5  # Sampling rate (≈29558.8 Hz)
        N = 4096
        window = np.hanning(N)

        x = data[0:N] * window

        X = np.fft.fft(x)
        PSD = np.abs(X)**2 / (N * Fs)
        PSD_log = 10 * np.log10(PSD + 1e-12)
        PSD_shifted = np.fft.fftshift(PSD_log)

        # Frequency axis
        freq = np.fft.fftshift(np.fft.fftfreq(N, 1/Fs))

        freq_welch, Pxx = welch(data, fs=Fs, window='hann',nperseg=N, noverlap=N//2)
        Pxx_dB = 10 * np.log10(Pxx + 1e-12)
        self.line_graph(freq,PSD_shifted)

    def spectrogram_from_data(self,data,samping_size):

        self.spectrogram_layout.clear()
    
        f, time_bins, Sxx = spectrogram(data, fs=samping_size, nperseg=2048, noverlap=1024, nfft=2048)
        Sxx_db = 10 * np.log10(Sxx + 1e-12)

        # quantizes to courser bins
        # (bigger freq bin factor = coarser/blockier and vice versa)
        freq_bin_factor = 256   # average 16 FFT bins together
        f_trim = f[:len(f)//freq_bin_factor * freq_bin_factor] 
        S_trim = Sxx_db[:len(f_trim), :len(time_bins)]

        #average the freq bins
        S_coarse = S_trim.reshape(
            len(f_trim)//freq_bin_factor, freq_bin_factor,
            len(time_bins)
        ).mean(axis=1)

        #threshold
        threshold = Sxx_db.mean()+1
        print(threshold)
        occupancy = (S_coarse > threshold).astype(float)
        print(Sxx_db.max())
        
        plot = self.spectrogram_layout.addPlot(title="RF View")
        plot.setLabel('left', 'Frequency (kHz)')
        plot.setLabel('bottom', 'Time (s)')
        plot.showGrid(x=True, y=True)

        img = pg.ImageItem()
        plot.addItem(img)

        # Set up colormap and levels
        lut = pg.colormap.get('inferno').getLookupTable(0.0, 1.0, 256)
        img.setLookupTable(lut)
        img.setLevels([0, 1])

        # display data
        img.setImage(occupancy)
        
        time_step = time_bins[1] - time_bins[0]  
        img.setRect(QtCore.QRectF(
            time_bins[0],               
            f_trim[0] / 1e3,           
            time_step * occupancy.shape[1],   
            (f_trim[-1] - f_trim[0]) / 1e3 
        ))
                
        self.spectrogram_layout.addItem(plot)

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
                fs = f[key]["fs"][0]
                self.max_index = len(f[key]['iq_data_len'])

                #self.psdAndFreq(data)
                self.spectrogram_from_data(data,fs)
                #self.spectrogram_from_synthetic_data()
        except Exception as e:
            print(f"Error loading or plotting file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())