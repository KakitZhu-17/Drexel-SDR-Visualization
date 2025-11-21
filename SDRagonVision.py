import sys
from PyQt5.QtWidgets import QMainWindow,QTabWidget,QApplication, QWidget,QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt
import h5py
import pyqtgraph as pg
import numpy as np
from scipy.signal import spectrogram

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
    
def signal_generator(start, end, fs=1e6, freq=200e3, sigtype="simple",duration = 2):
    if sigtype == "burst":
        total_N = int(fs * duration)
        t = np.arange(total_N) / fs

        burst = np.zeros(total_N)
        s = int(start * fs)
        e = int(end * fs)

        tone = np.sin(2*np.pi*freq*t)
        burst[s:e] = tone[s:e]

        return burst, fs

    if sigtype == "simple":
        fs = 1e6
        N = 1024 * 1000
        t = np.arange(N) / fs
        f = 50e3
        x = np.sin(2*np.pi*f*t) + 0.2*np.random.randn(len(t))
        return x, fs
    

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDRagon Vision")
        self.index = 0
        self.max_index = None
        self.current_file_path = None
        self.global_time = 0
        self.bin_factor = 128
        self.colormap_scheme = "magma"

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #07294D; color: #FFC600;") #works like css stylesheets

        self.load_button = QPushButton("Load Log File")
        self.load_button.setStyleSheet("background-color: #006699; color: #FFC600;")
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)

        #buttons for transmitter (for mock up only, delete later)

        self.horizonal_layout = QHBoxLayout()

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
            

    def binary_occupancy_from_data(self,data,sample_rate):
        self.binary_occupany_layout.clear()
        self.ob_plot = self.binary_occupany_layout.addPlot(title="RF View")

        f,time_bins,Sxx_db = calculate_spectrogram(data,sample_rate)
        freq_bin_factor = self.bin_factor        
        F = len(f)
        T = len(time_bins)
        F_trim = (F // freq_bin_factor) * freq_bin_factor
        f_trim = f[:F_trim]
        S_trim = Sxx_db[:F_trim,:T]     

        f_coarse = f_trim.reshape(-1, freq_bin_factor).mean(axis=1) 
        S_coarse = S_trim.reshape(len(f_coarse), freq_bin_factor, T).max(axis=1)  

        thr_offset_db = -5   # try -2 to -6 but this will change later on
        threshold = np.max(S_coarse)+thr_offset_db
        occupancy = (S_coarse > threshold).astype(float)
        
        plot = self.ob_plot
        img = pg.ImageItem()
        plot.addItem(img)
        img.setColorMap(self.colormap_scheme)
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

        self.global_time += time_bins[-1]
                        
        self.binary_occupany_layout.addItem(plot)


    def append_data_binary_occupany(self,data,sample_rate):
        plot = self.ob_plot
        f, time_bins, Sxx_db = calculate_spectrogram(data, sample_rate)

        freq_bin_factor = self.bin_factor
        F = len(f)
        T = len(time_bins)
        F_trim = (F // freq_bin_factor) * freq_bin_factor
        f_trim = f[:F_trim]
        S_trim = Sxx_db[:F_trim, :T]

        f_coarse = f_trim.reshape(-1, freq_bin_factor).mean(axis=1)
        S_coarse = S_trim.reshape(len(f_coarse), freq_bin_factor, T).max(axis=1)

        threshold = np.max(S_coarse) - 5
        occupancy = (S_coarse > threshold).astype(float)

        img = pg.ImageItem()
        img.setColorMap(self.colormap_scheme)
        img.setImage(occupancy.T)

        sample_time_width = len(data) / sample_rate 
        print(sample_time_width,time_bins[-1])   
        start_time = self.global_time               
        self.global_time += time_bins[-1]            

        img.setRect(pg.QtCore.QRectF(
            start_time,
            f[0]/1e3,
            time_bins[-1],                                
            (f[-1] - f[0]) / 1e3
        ))

        plot.addItem(img)
        plot.setXRange(self.global_time-time_bins[-1], self.global_time)


    def spectrogram_from_data(self,data,sample_rate):
        
        self.setup_spectrogram.clear()
        self.spectrogram = self.setup_spectrogram.addPlot(title="Spectrogram")
        f,time_bins,Sxx_db = calculate_spectrogram(data,sample_rate)
        
        plot = self.spectrogram
        plot.setLabel("left", "Frequency (kHz)")
        plot.setLabel("bottom", "Time (s)")

        img = pg.ImageItem()
        plot.addItem(img)
        cmap = pg.colormap.get(self.colormap_scheme)
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
                fs = f[key]["fs"][self.index]
                self.max_index = len(data)
                if(data.dtype == "int8"):
                    sample = data
                    if len(data) % 2 != 0:
                        sample = data[:-1]
                    iq_data = sample[::2] + 1j*sample[1::2]
                    iq_data = iq_data /128
                
                    if(self.index == 0):
                        self.binary_occupancy_from_data(iq_data,fs)
                    else:
                        #print("not first")
                        self.append_data_binary_occupany(iq_data,fs)
                    self.spectrogram_from_data(iq_data,fs)
                elif(data.dtype == "complex64"):
                    if(self.index == 0):
                        self.binary_occupancy_from_data(data,fs)
                    else:
                        self.append_data_binary_occupany(data,fs)
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