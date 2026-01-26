import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from initial import initial_fields
import numpy as np

class RF_view(initial_fields):
    def __init__(self):
        super().__init__()
        self.RF_widget = None
        self.index= None
        self.max_index= None

    def RF_view_tab(self):
        #this is basically how you add a widget
        tab = QWidget()
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout() #this is a vertical layout box, it puts widgets on top of each other
        layout.addWidget(self.binary_occupany_layout)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "RF view")
        self.RF_widget = self.binary_occupany_layout.addPlot(title="RF View")
        self.RF_widget.setLabel("left", "Frequency (kHz)")
        self.RF_widget.setLabel("bottom", "Time (s)")

    def RF_view_tab_setup(self):
        #this is basically how you add a widget
        tab = QWidget()
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout = QVBoxLayout() #this is a vertical layout box, it puts widgets on top of each other
        layout.addWidget(self.binary_occupany_layout)
        tab.setLayout(layout)
        #self.tabs.addTab(tab, "RF view")
        self.RF_widget = self.binary_occupany_layout.addPlot(title="RF View")
        self.RF_widget.setLabel("left", "Frequency (kHz)")
        self.RF_widget.setLabel("bottom", "Time (s)")
        return tab

    def append_data_binary_occupany(self,f,time_bins,Sxx_db,timestamps):

        plot = self.RF_widget 

        if(self.index == 0):
            self.RF_widget.clear()
            viewbox_call=plot.getViewBox()
            viewbox_call.setLimits(xMin=timestamps[0],xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
            #viewbox_call.sigRangeChanged.connect(self.update_view_range)
            plot.setXRange(timestamps[0], timestamps[0]+time_bins[-1],padding=0)

        occupancy = (Sxx_db > -110 ).astype(float)

        img = pg.ImageItem()
        img.setColorMap("magma")
        img.setImage(occupancy.T)

        start_time = 0   

        freq_step = (f[-1] - f[0])

        img.setRect(pg.QtCore.QRectF(
            timestamps[self.index],
            f[0]/1e3,
            time_bins[-1],                                
            freq_step/ 1e3
        ))

        plot.addItem(img)
    

    

   
