import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from initial import initial_fields

class spectrogram(initial_fields):
    def __init__(self):
        super().__init__()

    def spectrogram_tab(self):
        tab = QWidget()
        self.setup_spectrogram = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout()
        layout.addWidget(self.setup_spectrogram)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Spectrogram")
        self.spectrogram = self.setup_spectrogram.addPlot(title="Spectrogram")
        self.spectrogram.setLabel("left", "Frequency (kHz)")
        self.spectrogram.setLabel("bottom", "Time (s)")
        self.images = []


    def spectrogram_from_file(self,f,time_bins,Sxx_db,timestamps):
        
        self.setup_spectrogram.clear()
        self.spectrogram = self.setup_spectrogram.addPlot(title="Spectrogram")
        
        plot = self.spectrogram

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
            timestamps[self.index],       
            f[0]/1e3,       
            time_bins[-1],   
            freq_step/1e3
        ))
             
        self.setup_spectrogram.addItem(plot)
        #self.setup_spectrogram.addItem(colorbar)

    def plot_all_spectrogram(self,f,time_bins,Sxx_db,timestamps):
        
        plot = self.spectrogram

        if(self.index == 0):
            self.setup_spectrogram.clear()

        img = pg.ImageItem()
        plot.addItem(img)
        cmap = pg.colormap.get(self.colormap_scheme)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        img.setLookupTable(lut)
        img.setImage(Sxx_db.T)
        
        freq_step = (f[-1] - f[0])

        img.setRect(pg.QtCore.QRectF(
            timestamps[self.index],       
            f[0]/1e3,       
            time_bins[-1],   
            freq_step/1e3
        ))

        self.setup_spectrogram.addItem(plot)

        self.images.append(img)

        if(self.index == self.max_index-1):
            viewbox_call=plot.getViewBox()
            viewbox_call.setLimits(xMin=0,xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
            plot.setXRange(timestamps[0], timestamps[0]+time_bins[-1],padding=0)
            colorbar = pg.ColorBarItem(
                values=(0, Sxx_db.max()), 
                colorMap= cmap,
                label="Power (dB)"
            )
            colorbar.setImageItem(self.images)
            self.setup_spectrogram.addItem(colorbar)
        


   
