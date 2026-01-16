import dragonradio.tools.mgen as mgen
import pandas as pd
import numpy as np
import PyQt5
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5 import QtCore
import pyqtgraph as pg
from initial import initial_fields
import os

class linked_view(initial_fields):
    def __init__(self):
        super().__init__()

    def linked_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.setup_linked_traffic = pg.PlotWidget()
        self.linked_binary_occupany_layout = pg.GraphicsLayoutWidget(title="Spectrogram")
        layout.addWidget(self.setup_linked_traffic)
        layout.addWidget(self.linked_binary_occupany_layout)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "linked view")
        self.setup_linked_traffic.setMouseEnabled(x=False, y=False)
        self.setup_linked_traffic.setLabel("left", "Mbps")
        self.setup_linked_traffic.setLabel("bottom", "Time (s)")

    def linked_traffic_from_file(self,file_path):
        
        self.setup_linked_traffic.clear()

        send_arr = mgen.parseSend(file_path)
        send_df = pd.DataFrame(send_arr).astype({ 'timestamp': 'datetime64[ns, UTC]'}, copy=False)
        traffic_arr = send_df.to_numpy()
        plot = self.setup_linked_traffic
        datetime = send_df['timestamp']
        dt_array_ns_UTC = np.array(datetime, dtype='datetime64[ns]')
        elapsed_time_timedelta = dt_array_ns_UTC - dt_array_ns_UTC[0]
        #print(elapsed_time_timedelta)
        time_seconds= elapsed_time_timedelta / np.timedelta64(1, 's')
        
        plot.plot(x=time_seconds.astype(float),y=traffic_arr[:,1].astype(int),pen=pg.mkPen('c', width=2))

        bargraph = pg.BarGraphItem(x=time_seconds.astype(float), height=traffic_arr[:,-1].astype(int), width=0.001,brush="blue",pen=None)
        plot.addItem(bargraph)
        bargraph.setOpacity(0.3)

    def traffic_logs_from_file_linked(self,file_path):
        plot = self.setup_linked_traffic
        plot.clear()
        try:
            files = [f for f in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, f))]
            send_arr = mgen.parseSend(file_path+"/"+files[0])
            send_df = pd.DataFrame(send_arr).astype({ 'timestamp': 'datetime64[ns, UTC]'}, copy=False)
            send_traffic_arr = send_df.to_numpy()
            send_datetime = send_df['timestamp']
            send_dt_array_ns_UTC = np.array(send_datetime, dtype='datetime64[ns]')
            send_elapsed_time_timedelta = send_dt_array_ns_UTC - send_dt_array_ns_UTC[0]
            send_time_seconds= send_elapsed_time_timedelta / np.timedelta64(1, 's')

            recv_arr = mgen.parseRecv(file_path+"/"+files[1])
            recv_df = pd.DataFrame(recv_arr).astype({ 'timestamp': 'datetime64[ns, UTC]'}, copy=False)
            #print(recv_df)
            recv_traffic_arr = recv_df.to_numpy()
            recv_datetime = recv_df['timestamp']
            recv_dt_array_ns_UTC = np.array(recv_datetime, dtype='datetime64[ns]')
            recv_elapsed_time_timedelta = recv_dt_array_ns_UTC - recv_dt_array_ns_UTC[0]
            recv_time_seconds= recv_elapsed_time_timedelta / np.timedelta64(1, 's')

            latency_dt = recv_datetime - send_datetime
            latency_td = latency_dt/np.timedelta64(1, 's')
            latency=latency_td.dropna().to_numpy()

            plot.plot(x=send_time_seconds.astype(float),y=send_traffic_arr[:,1].astype(int),pen=(255, 0, 0, 150)) #flow line for send
            plot.plot(x=recv_time_seconds.astype(float),y=recv_traffic_arr[:,1].astype(int),pen=(0, 0, 255, 150)) #flow line for recv/listen
            plot.plot(x=send_time_seconds.astype(float),y=send_traffic_arr[:,-1].astype(int),pen=pg.mkPen(color=(0, 100, 220), width=1, style=QtCore.Qt.DashLine),fillLevel=0,brush=pg.mkBrush(color=(0, 100, 200,30))) #size in time for send
            recv_bargraph = pg.BarGraphItem(x=recv_time_seconds.astype(float), height=recv_traffic_arr[:,-1].astype(int), width=0.0008,brush="blue",pen=None)

            plot.addItem(recv_bargraph)
            recv_bargraph.setOpacity(0.5)
           
            plot.plot(x=recv_time_seconds.astype(float),y=latency.astype(float),pen=(255, 255, 255, 200)) #latency in time line
            plot.setXRange(self.current_x_range[0], self.current_x_range[0]+self.time_step,padding=0)
        except Exception as e:
            print("test error:",e)
   

    def update_line_view_range(self):
        self.current_line_x_range = self.linked_ob_plot.viewRange()[0]

    def update_traffic_linked(self):
        self.setup_linked_traffic.setXRange(self.current_line_x_range[0], self.current_line_x_range[0]+self.time_step,padding=0)

    def linked_binary_occupancy_from_file(self,f,time_bins,Sxx_db,timestamps):
        self.linked_binary_occupany_layout.clear()
        self.linked_ob_plot = self.linked_binary_occupany_layout.addPlot(title="RF View")

        threshold = np.mean(Sxx_db)
        self.dB_spin_box.setValue(int(threshold))
        threshold = self.threshold
        occupancy = (Sxx_db > threshold).astype(float)
        
        plot = self.linked_ob_plot
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
        
        self.linked_binary_occupany_layout.addItem(plot)
        viewbox_call=plot.getViewBox()
        viewbox_call.setLimits(xMin=timestamps[0],xMax=timestamps[0]+time_bins[-1] ,yMin=f.min()/1e3, yMax=f.max()/1e3)
        viewbox_call.sigRangeChanged.connect(self.update_line_view_range)
        viewbox_call.sigRangeChanged.connect(self.update_traffic_linked)
    
    def linked_append_data_binary_occupany(self,f,time_bins,Sxx_db):
        plot = self.linked_ob_plot

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
