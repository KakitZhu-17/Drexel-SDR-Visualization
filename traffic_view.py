import dragonradio.tools.mgen as mgen
import pandas as pd
import numpy as np
import PyQt5
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from initial import initial_fields
import os
from PyQt5 import QtCore

class Traffic_view(initial_fields):
    def __init__(self):
        super().__init__()
        self.throughput_widget = None
        self.ibw_widget = None
        self.linked_spectrogram = None
        self.linked_spectrogram_plot = None

    def traffic_tab(self):
        tab = QWidget()
        self.throughput_widget = pg.PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.throughput_widget)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Traffic View")
        self.throughput_widget.setLabel("left", "bytes")
        self.throughput_widget.setLabel("bottom", "Time (s)")

    def traffic_tab_setup(self):
        tab = QWidget()
        self.throughput_widget = pg.PlotWidget()
        self.ibw_widget = pg.PlotWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.throughput_widget)
        self.layout.addWidget(self.ibw_widget)
        tab.setLayout(self.layout)
        self.throughput_widget.setLabel("left", "bytes")
        self.throughput_widget.setLabel("bottom", "Time (s)")

        self.ibw_widget.setLabel("left", "mbps")
        self.ibw_widget.setLabel("bottom", "Time (s)")
        return tab

    def add_widget(self,tab_ref,plot_ref):
        self.linked_spectrogram = tab_ref
        self.linked_spectrogram_plot = plot_ref
        self.layout.addWidget(self.linked_spectrogram)


    def update_traffic_view_range(self,start,end):
        self.throughput_widget.setXRange(start, end,padding=0)
        self.ibw_widget.setXRange(start, end,padding=0)
        self.linked_spectrogram_plot.spectrogram_widget.setXRange(start, end,padding=0)


    def traffic_from_file(self,file_path):
        
        self.throughput_widget.clear()
        self.ibw_widget.clear()
        try:
            send_arr = mgen.parseSend(file_path)
            
            send_df = pd.DataFrame(send_arr).astype({ 'timestamp': 'datetime64[ns, UTC]'}, copy=False)
            traffic_arr = send_df.to_numpy()
            
            throughput_plot = self.throughput_widget
            datetime = send_df['timestamp']
            
            send_dt_array_ns_UTC = np.array(datetime, dtype='datetime64[ns]')
           
            send_elapsed_time_timedelta = send_dt_array_ns_UTC - send_dt_array_ns_UTC[0]
            send_time_seconds= send_elapsed_time_timedelta / np.timedelta64(1, 's')
            throughput_plot.plot(x=send_time_seconds.astype(float),y=traffic_arr[:,1].astype(int),pen=pg.mkPen('c', width=2))
            bargraph = pg.BarGraphItem(x=send_time_seconds.astype(float), height=traffic_arr[:,-1].astype(int), width=0.001,brush="blue",pen=None)
            throughput_plot.addItem(bargraph)
            bargraph.setOpacity(0.3)
        except Exception as e:
            print("test error:",e)

    def traffic_logs_from_file(self,file_path):
        throughput_plot = self.throughput_widget
        throughput_plot.clear()

        ibw_plot = self.ibw_widget
        ibw_plot.clear()
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
            recv_traffic_arr = recv_df.to_numpy()
            recv_datetime = recv_df['timestamp']
            recv_dt_array_ns_UTC = np.array(recv_datetime, dtype='datetime64[ns]')
            recv_elapsed_time_timedelta = recv_dt_array_ns_UTC - recv_dt_array_ns_UTC[0]
            recv_time_seconds= recv_elapsed_time_timedelta / np.timedelta64(1, 's')

            windowed_recv_time=recv_time_seconds//0.2
            windowed_recv_size=(np.bincount(windowed_recv_time.astype(int),weights=recv_traffic_arr[:,-1].astype(int)) *8 )/0.2
            array_in_seconds = np.arange(len(windowed_recv_size))

            latency_dt = recv_datetime - send_datetime
            latency_td = latency_dt/np.timedelta64(1, 's')
            latency=latency_td.dropna().to_numpy()

            #throughput_plot.throughput_plot(x=send_time_seconds.astype(float),y=send_traffic_arr[:,1].astype(int),pen=(255, 0, 0, 150)) #flow line for send
            #throughput_plot.throughput_plot(x=recv_time_seconds.astype(float),y=recv_traffic_arr[:,1].astype(int),pen=(0, 0, 255, 150)) #flow line for recv/listen
            
            ibw_plot.plot(x=array_in_seconds/5,y=windowed_recv_size/1e6,pen=(255, 255, 255, 150)) #instantious bandwidth

            throughput_plot.plot(x=send_time_seconds.astype(float),y=send_traffic_arr[:,-1].astype(int),pen=pg.mkPen(color=(0, 100, 220), width=1, style=QtCore.Qt.DashLine),fillLevel=0,brush=pg.mkBrush(color=(0, 100, 200,30))) #size in time for send
            throughput_plot.plot(x=recv_time_seconds.astype(float),y=recv_traffic_arr[:,-1].astype(int),pen=pg.mkPen(color=(220, 220, 0)),fillLevel=0,brush=pg.mkBrush(color=(200,200,0,10))) #size in time for recv
        
            throughput_plot.plot(x=recv_time_seconds.astype(float),y=latency.astype(float),pen=(255, 0, 0, 200)) #latency in time line
        except Exception as e:
            print("test error:",e)
   
