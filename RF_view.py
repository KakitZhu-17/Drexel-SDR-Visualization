import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from initial import initial_fields
import numpy as np

class RF_view(initial_fields):
    def __init__(self):
        super().__init__()

    def RF_view_tab(self):
        #this is basically how you add a widget
        tab = QWidget()
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout() #this is a vertical layout box, it puts widgets on top of each other
        layout.addWidget(self.binary_occupany_layout)
        tab.setLayout(layout)
        # Changed to return tab
        return tab

    def binary_occupancy_from_file(self,f,time_bins,Sxx_db,timestamps):
        self.binary_occupany_layout.clear()
        self.ob_plot = self.binary_occupany_layout.addPlot(title="RF View")

        threshold = np.mean(Sxx_db)
        self.dB_spin_box.setValue(int(threshold))
        threshold = self.threshold
        occupancy = (Sxx_db > threshold).astype(float)
        
        plot = self.ob_plot
        img = pg.ImageItem()
        plot.addItem(img)
        img.setColorMap("magma")
        img.setImage(occupancy.T)
        plot.setLabel("left", "Frequency (kHz)")
        plot.setLabel("bottom", "Time (s)")
        freq_total = (f[-1] - f[0])

        #print(timestamps[0],timestamps[0]+time_bins[-1])
        
        img.setRect(pg.QtCore.QRectF(
            timestamps[0],
            f[0]/1e3,
            time_bins[-1],
            freq_total/1e3
        ))
        
        self.binary_occupany_layout.addItem(plot)
        viewbox_call=plot.getViewBox()
        viewbox_call.setLimits(xMin=timestamps[0],xMax=timestamps[0]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
        viewbox_call.sigRangeChanged.connect(self.update_view_range)
    
    def append_data_binary_occupany(self,f,time_bins,Sxx_db):
        plot = self.ob_plot

        #freq_bin_factor = self.bin_factor
        
        #F = len(f)
        #T = len(time_bins)

        #F_trim = (F // freq_bin_factor) * freq_bin_factor
        #f_trim = f[:F_trim]
        #S_trim = Sxx_db[:F_trim, :T]

        #f_coarse = f_trim.reshape(len(f_trim)//freq_bin_factor, freq_bin_factor).mean(axis=1)
        #S_coarse = S_trim.reshape(len(f_coarse), freq_bin_factor, T).max(axis=1)

        threshold = self.threshold
        occupancy = (Sxx_db > threshold).astype(float)

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

    

    

   
