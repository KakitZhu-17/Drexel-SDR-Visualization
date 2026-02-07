import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout,QHBoxLayout,QCheckBox
import pyqtgraph as pg
from initial import initial_fields
import numpy as np
import math_methods
from PyQt5.QtCore import Qt
from dragonradio.signal import decompressIQData

class all_view(initial_fields):
    def __init__(self):
        super().__init__()
        self.RF_widget = None
        self.index= None
        self.max_index= None
        self.current_file_index = 0
        self.file_image_index=0
        self.all_images = []
        self.check_boxes_arr=[]
        self.colors = [[255, 255, 0, 150],[0, 255, 0, 150],[0, 0, 255, 150],[0, 255, 255, 150],[255, 0, 255, 150]]

    def all_view_tab_setup(self):
        #this is basically how you add a widget
        tab = QWidget()
        
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="RF View")
        self.layout = QHBoxLayout() #this is a vertical layout box, it puts widgets on top of each other
        
        self.check_box_container = QWidget()
    
        self.layout.addWidget(self.check_box_container)
        self.check_box_layout = QVBoxLayout()
        self.check_box_container.setLayout(self.check_box_layout)

        self.layout.addWidget(self.binary_occupany_layout)
        tab.setLayout(self.layout)
        self.add_colorbar_check_box()

        self.RF_widget = self.binary_occupany_layout.addPlot(title="RF View")
        self.RF_widget.setLabel("left", "Frequency (kHz)")
        self.RF_widget.setLabel("bottom", "Time (s)")
        return tab


    def layer_append(self,f,time_bins,Sxx_db,timestamps,color_index):

        plot = self.RF_widget 
        threshold = -110

        if(self.index == 0):
            new_plot_obj = plot_images(color_index,self.check_box_layout)
            new_plot_obj.add_check_box()
            self.check_boxes_arr.append(new_plot_obj)

            viewbox_call=plot.getViewBox()
            viewbox_call.setLimits(xMin=timestamps[0],xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
            plot.setXRange(timestamps[0], timestamps[0]+time_bins[-1],padding=0)

        #occupancy = (Sxx_db > threshold ).astype(float)

        colors = np.array([
            [0, 0, 0, 0],  
            self.colors[color_index]  
        ])
        # Stops 0.0 and 1.0 map directly to the two colors
        cmap = pg.ColorMap(pos=np.array([0.0, 1.0]), color=colors)
        lut = cmap.getLookupTable(start=0.0, stop=1.0, nPts=256)

        img = pg.ImageItem()
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


        self.check_boxes_arr[color_index].plot_images.append(img)

        plot.addItem(img)

        if(self.index == self.max_index-1):
            colorbar = pg.ColorBarItem(
                #values=(Sxx_db.min(), Sxx_db.max()), 
                colorMap= cmap,
                label="Power (dB)"
            )
            colorbar.setImageItem(self.check_boxes_arr[color_index].plot_images)
            self.binary_occupany_layout.addItem(colorbar)
            self.check_boxes_arr[color_index].colorbar = colorbar

    def plot_all_data_from_file(self,file,index,max_index,color_index):
        timestamps = file['snapshots']['timestamp']
        data = file['snapshots']["iq_data"][index]
        fs = file['snapshots']["fs"][index]
        f,time_bins,Sxx_db = math_methods.calculate_spectrogram(decompressIQData(data),fs)
        #print(timestamps[0]+time_bins[-1])
        self.index = index
        self.max_index = max_index
        if(index < max_index):
            self.layer_append(f,time_bins,Sxx_db,timestamps,color_index)

    def add_colorbar_check_box(self):
        check_box = QCheckBox("Colorbars")
        check_box.setChecked(True)
        check_box.stateChanged.connect(self.toggle_colorbar)
        self.check_boxes_ref = check_box
        self.check_box_layout.addWidget(self.check_boxes_ref)

    def toggle_colorbar(self,state):
        if state == Qt.CheckState.Checked:
            for plot_obj in self.check_boxes_arr:
                if(plot_obj.colorbar != None):
                    plot_obj.colorbar.setVisible(True)
        else:
            for plot_obj in self.check_boxes_arr:
                if(plot_obj.colorbar != None):
                    plot_obj.colorbar.setVisible(False)

class plot_images():
    def __init__(self,num,widget_ref):
        self.slot_num = num
        self.plot_images = []
        self.colorbar = None
        self.check_boxes_ref = None
        self.plot_ref = widget_ref

    def add_check_box(self):
        title = "File " + str(self.slot_num+1)
        check_box = QCheckBox(title)
        check_box.setChecked(True)
        check_box.stateChanged.connect(self.toggle_update)
        self.check_boxes_ref = check_box
        self.plot_ref.addWidget(self.check_boxes_ref)


    def toggle_update(self,state):
        if state == Qt.CheckState.Checked:
            for image in self.plot_images:
                image.setVisible(True)
            #self.colorbar.setVisible(True)
        else:
            for image in self.plot_images:
                image.setVisible(False)
            #self.colorbar.setVisible(False)

   
