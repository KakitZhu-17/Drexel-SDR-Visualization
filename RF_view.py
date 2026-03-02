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
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="RF View")
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
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="RF View")
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
            viewbox_call.setLimits(xMin=0,xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
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

    def append_data_binary_occupany_test(self,f,time_bins,Sxx_db,timestamps,color_vec):

        plot = self.RF_widget 
        threshold = -110

        if(self.index == 0):
            #self.RF_widget.clear()
            viewbox_call=plot.getViewBox()
            viewbox_call.setLimits(xMin=timestamps[0],xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
            #viewbox_call.sigRangeChanged.connect(self.update_view_range)
            plot.setXRange(timestamps[0], timestamps[0]+time_bins[-1],padding=0)

        occupancy = (Sxx_db > threshold ).astype(float)

        colors = np.array([
            [0, 0, 0, 0],   # Low color (Red)
            color_vec    # High color (Blue)
        ])
        # Stops 0.0 and 1.0 map directly to the two colors
        cmap = pg.ColorMap(pos=np.array([0.0, 1.0]), color=colors)
        lut = cmap.getLookupTable(start=0.0, stop=1.0, nPts=256)

        img = pg.ImageItem()
        #img.setColorMap("magma")
        img.setLookupTable(lut)
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

    def layer_append(self,f,time_bins,Sxx_db,timestamps,color_vec):

        plot = self.RF_widget 
        threshold = -110

        if(self.index == 0):
            viewbox_call=plot.getViewBox()
            viewbox_call.setLimits(xMin=timestamps[0],xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
            plot.setXRange(timestamps[0], timestamps[0]+time_bins[-1],padding=0)

        occupancy = (Sxx_db > threshold ).astype(float)

        colors = np.array([
            [0, 0, 0, 0],  
            color_vec  
        ])
        # Stops 0.0 and 1.0 map directly to the two colors
        cmap = pg.ColorMap(pos=np.array([0.0, 1.0]), color=colors)
        lut = cmap.getLookupTable(start=0.0, stop=1.0, nPts=256)

        img = pg.ImageItem()
        #img.setColorMap("magma")
        img.setLookupTable(lut)
        #img.setImage(occupancy.T)
        img.setImage(Sxx_db.T)
        img.setZValue(np.nanmax(Sxx_db.T))


        start_time = 0   

        freq_step = (f[-1] - f[0])

        img.setRect(pg.QtCore.QRectF(
            timestamps[self.index],
            f[0]/1e3,
            time_bins[-1],                                
            freq_step/ 1e3
        ))

        plot.addItem(img)
   
