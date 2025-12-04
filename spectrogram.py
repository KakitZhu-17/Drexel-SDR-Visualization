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
        self.tabs.addTab(tab, "spectrogram")


    def spectrogram_from_file(self,f,time_bins,Sxx_db):
        
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

   
