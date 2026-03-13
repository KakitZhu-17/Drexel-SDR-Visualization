import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout,QHBoxLayout,QCheckBox,QSlider,QLabel,QProgressBar,QFrame
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
        self.check_boxes_arr=[]
        self.colors = [[255, 255, 0, 255],[0, 0, 255, 255],[0, 255, 0, 255],[0, 255, 255, 255],[255, 0, 255, 255],[255, 255, 255, 255]]
        self.max_db = None
        self.min_db = None
        self.global_max_time = 0

    def all_view_tab_setup(self):
        #this is basically how you add a widget
        tab = QWidget()
        
        self.binary_occupany_layout = pg.GraphicsLayoutWidget(title="RF View")
        self.layout = QVBoxLayout() #this is a vertical layout box, it puts widgets on top of each other
        
        self.check_box_container = QWidget()
    
        self.layout.addWidget(self.check_box_container)
        self.check_box_layout = QHBoxLayout()
        self.check_box_layout.setSpacing(0)
        self.check_box_layout.setContentsMargins(0, 0, 0, 0)
        self.check_box_container.setLayout(self.check_box_layout)
        self.check_box_container.setFixedSize(1000,70)

        self.layout.addWidget(self.binary_occupany_layout)
        tab.setLayout(self.layout)
        #self.add_colorbar_check_box()

        self.RF_widget = self.binary_occupany_layout.addPlot(title="All View")
        self.RF_widget.setLabel("left", "Frequency (kHz)")
        self.RF_widget.setLabel("bottom", "Time (s)")
    
        self.time_line = pg.InfiniteLine(
            pos=(self.RF_widget.viewRange()[0][0] + self.RF_widget.viewRange()[0][1])/2, 
            angle=90, 
            movable=True, 
            pen=pg.mkPen('w', width=3)
        )
        #self.time_line.sigPositionChanged.connect(self.time_line_update)
        self.RF_widget.addItem(self.time_line)

        self.global_colorbar()

        return tab


    def calculate_opacity(self):
        diff = abs(self.min_db) - abs(self.max_db)
        for plot_obj in self.check_boxes_arr:
            for images in plot_obj.plot_images:
                index_opacity = (images.image.max()+abs(self.min_db))/diff 
                #print("opacity val ",index_opacity)
                images.setOpacity(index_opacity)

    def layer_append(self,f,time_bins,Sxx_db,timestamps,color_index,node_id):

        plot = self.RF_widget 

        if(self.index == 0):
            new_plot_obj = plot_images(color_index,self.check_box_layout,node_id)
            new_plot_obj.add_check_box()
            self.check_boxes_arr.append(new_plot_obj)

            if(self.min_db == None):
                self.min_db = Sxx_db.min()
            if((self.max_db == None)):
                self.max_db = Sxx_db.max()

            self.global_colorbar.setLevels(low=self.min_db,high=self.max_db)

            viewbox_call=plot.getViewBox()
            if(timestamps[-1]+time_bins[-1] > self.global_max_time):
                viewbox_call.setLimits(xMin=0,xMax=timestamps[-1]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
                self.global_max_time = timestamps[-1]+time_bins[-1]
            
            plot.setXRange(timestamps[0], timestamps[0]+time_bins[-1],padding=0)
            self.time_line.setValue((self.RF_widget.viewRange()[0][0] + self.RF_widget.viewRange()[0][1])/2)

        colors = np.array([
            [0, 0, 0, 0],  
            self.colors[color_index]  
        ])

        cmap = pg.ColorMap(pos=np.array([0.0, 1.0]), color=colors)
        lut = cmap.getLookupTable(start=0.0, stop=1.0, nPts=256)

        img = pg.ImageItem()
        img.setLookupTable(lut)
        img.setImage(Sxx_db.T)
        img.setZValue(np.nanmax(Sxx_db.T))

        freq_step = (f[-1] - f[0])

        img.setRect(pg.QtCore.QRectF(
            timestamps[self.index],
            f[0]/1e3,
            time_bins[-1],                                
            freq_step/ 1e3
        ))

        self.check_boxes_arr[color_index].plot_images.append(img)

        plot.addItem(img)

        #print(Sxx_db.min(),Sxx_db.max())
        if((self.min_db > Sxx_db.max())):
            self.min_db = Sxx_db.min()
            self.global_colorbar.setLevels(low=self.min_db,high=self.max_db)
        if((self.max_db < Sxx_db.max())):
            self.max_db = Sxx_db.max()
            self.global_colorbar.setLevels(low=self.min_db,high=self.max_db)

        if(self.index == self.max_index-1):
            
            colorbar = pg.ColorBarItem(
                values=(self.global_colorbar.levels()),
                colorMap= cmap,
                label="Power (dB)",
            )
            colorbar.setImageItem(self.check_boxes_arr[color_index].plot_images)
            colorbar.setVisible(False)
            
            self.calculate_opacity()
        
            self.binary_occupany_layout.addItem(colorbar)
            self.check_boxes_arr[color_index].colorbar = colorbar
            self.update_all_colorbar_range(self.global_colorbar)
        
        

    def global_colorbar(self):
        #global colorbar
        colors = np.array([
            [0, 0, 0, 0],  
           [255,255,255,255]  
        ])
        cmap = pg.ColorMap(pos=np.array([0.0, 1.0]), color=colors)
        self.global_colorbar = pg.ColorBarItem(colorMap=cmap,label="Power (dB)")
        self.global_colorbar.sigLevelsChanged.connect(self.update_all_colorbar_range)
        
        self.binary_occupany_layout.addItem(self.global_colorbar)

    def update_all_colorbar_range(self,cb):
        for plot_obj in self.check_boxes_arr:
            if(plot_obj.colorbar != None):
                plot_obj.colorbar.setLevels(cb.levels())


    def plot_all_data_from_file(self,f,time_bins,Sxx_db,timestamps,index,max_index,color_index,node_id):
        self.index = index
        self.max_index = max_index
        if(index < max_index):
            self.layer_append(f,time_bins,Sxx_db,timestamps,color_index,node_id)

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
    
    def update_progressbar_value(self,index,value):
        self.check_boxes_arr[index].progressbar.setValue(value)
        #print(self.check_boxes_arr[index].progressbar.value())
        display_value= self.check_boxes_arr[index].progressbar.value()
        self.check_boxes_arr[index].progressbar.setFormat(f"{display_value/100}")


class plot_images():
    def __init__(self,num,widget_ref,node_id):
        self.slot_num = num
        self.plot_images = []
        self.node_id = node_id
        self.colorbar = None
        self.css_colors = ["yellow","blue","green","cyan","magenta","white"]

        self.progressbar = QProgressBar()
        self.progressbar.setFixedSize(25,20)
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(200)
        self.progressbar.setValue(0)
        self.progressbar.setFormat("%v")
        self.progressbar.setOrientation(Qt.Vertical)
        self.progressbar.setStyleSheet(f"""QProgressBar::chunk {{background-color: {self.css_colors[self.slot_num]};}}""")

        self.check_boxes_ref = None
        self.plot_ref = widget_ref
        self.slot_box = QFrame()
        self.slot_box.setFrameStyle(QFrame.WinPanel | QFrame.Raised)
        self.slot_box.setLineWidth(1) 
        self.slot_layout = QVBoxLayout()

    def add_check_box(self):
        title = "Node-" + str(self.node_id)
        check_box = QCheckBox(title)
        check_box.setChecked(True)
        check_box.setStyleSheet(f"""QCheckBox::indicator:checked {{background-color: {self.css_colors[self.slot_num]};}}""")
        check_box.stateChanged.connect(self.toggle_update)
        
        self.check_boxes_ref = check_box
        self.slot_layout.addWidget(check_box)
        self.slot_layout.addWidget(self.progressbar)
        self.slot_box.setLayout(self.slot_layout)
        self.slot_box.setFixedSize(90,70)

        self.plot_ref.addWidget(self.slot_box)


    def toggle_update(self,state):
        if state == Qt.CheckState.Checked:
            for image in self.plot_images:
                image.setVisible(True)
            #self.colorbar.setVisible(True)
        else:
            for image in self.plot_images:
                image.setVisible(False)
            #self.colorbar.setVisible(False)

   
