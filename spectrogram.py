import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from initial import initial_fields

class spectrogram(initial_fields):
    def __init__(self):
        super().__init__()
        self.spectrogram_widget = None
        self.index= None
        self.max_index= None

    def spectrogram_tab(self):
        tab = QWidget()
        self.setup_spectrogram = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout()
        layout.addWidget(self.setup_spectrogram)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Spectrogram")
        self.spectrogram_widget = self.setup_spectrogram.addPlot(title="Spectrogram")
        self.spectrogram_widget.setLabel("left", "Frequency (kHz)")
        self.spectrogram_widget.setLabel("bottom", "Time (s)")

    def spectrogram_tab_setup(self):
        tab = QWidget()
        self.setup_spectrogram = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout()
        layout.addWidget(self.setup_spectrogram)
        tab.setLayout(layout)
        self.spectrogram_widget = self.setup_spectrogram.addPlot()
        self.spectrogram_widget.setLabel("left", "Frequency (kHz)")
        self.spectrogram_widget.setLabel("bottom", "Time (s)")
        return tab

    def append_spectrogram(self,f,time_bins,Sxx_db,timestamps):
        
        plot = self.spectrogram_widget

        if(self.index == 0):
            self.setup_spectrogram.clear()
            viewbox_call=plot.getViewBox()
            viewbox_call.setLimits(xMin=0,xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
            #viewbox_call.sigRangeChanged.connect(self.update_view_range)
            plot.setXRange(timestamps[0], timestamps[0]+time_bins[-1],padding=0)

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
            colorbar = pg.ColorBarItem(
                values=(Sxx_db.min(), Sxx_db.max()), 
                colorMap= cmap,
                label="Power (dB)"
            )
            colorbar.setImageItem(self.images)
            self.setup_spectrogram.addItem(colorbar)
        
        #print(self.index, timestamps[self.index])
        


   
