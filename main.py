import sys
from PyQt5.QtWidgets import QApplication,QHBoxLayout
from PyQt5.QtCore import Qt
from ui_components import ui_components
from spectrogram import spectrogram
from RF_view import RF_view
from traffic_view import Traffic_view
#from linked_view import linked_view 


class MainWindow(ui_components,spectrogram,RF_view,Traffic_view):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDRagon Vision")

        #===============actual layout stuff===================================

        self.set_central_widget()

        self.loading_button()
        self.load_traffic_log_button()

        self.tab_container()

        #the actual plots
        self.RF_view_tab()
        self.spectrogram_tab()
        self.traffic_tab()
        #self.linked_tab()

        #threhold adjuster
        #self.setup_threshold_incrementor()

        #self.threshold_box = QHBoxLayout()
        #self.threshold_box.addLayout(self.dB_incrementer)

        #self.threshold_box.addWidget(self.tabs)
        #self.layout.addLayout(self.threshold_box)

        #self.time_progress_slider_setup()
        self.time_stretcher_setup()
        #self.index_controls()

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())