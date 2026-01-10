import dragonradio.tools.mgen as mgen
import pandas as pd
import numpy as np
import PyQt5
import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from initial import initial_fields

#file_name = "send.drc"

#send_arr = mgen.parseSend(file_name)
#send_df = pd.DataFrame(send_arr).astype({ 'timestamp': 'datetime64[ns, UTC]'}, copy=False)
#test = send_df.to_numpy()
#print(send_arr)
#print(test[:,0])
#print(test[:,-1])


class Traffic_view(initial_fields):
    def __init__(self):
        super().__init__()

    def traffic_tab(self):
        tab = QWidget()
        self.setup_traffic = pg.PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.setup_traffic)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Traffic View")


    def traffic_from_file(self,file_path):
        
        self.setup_traffic.clear()

        send_arr = mgen.parseSend(file_path)
        send_df = pd.DataFrame(send_arr).astype({ 'timestamp': 'datetime64[ns, UTC]'}, copy=False)
        traffic_arr = send_df.to_numpy()
        #print(send_df)
        plot = self.setup_traffic
        datetime = send_df['timestamp']
        #print(datetime.dtype)
        dt_array_ns_UTC = np.array(datetime, dtype='datetime64[ns]')
        #print(dt_array_ns_UTC)
        elapsed_time_timedelta = dt_array_ns_UTC - dt_array_ns_UTC[0]
        #print(elapsed_time_timedelta)
        time_seconds= elapsed_time_timedelta / np.timedelta64(1, 's')
        #print(time_seconds.astype(float))
        #test=datetime.to_numpy(dtype=int)
        plot.plot(x=time_seconds.astype(float),y=traffic_arr[:,1].astype(int),pen=pg.mkPen('c', width=2))
        #plot.showGrid(True)
        bargraph = pg.BarGraphItem(x=time_seconds.astype(float), height=traffic_arr[:,-1].astype(int), width=0.001,brush="blue",pen=None)
        plot.addItem(bargraph)
        bargraph.setOpacity(0.3)
        plot.setXRange(self.current_x_range[0], self.current_x_range[0]+self.time_step,padding=0)
   
