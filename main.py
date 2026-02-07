import sys
from PyQt5.QtWidgets import QApplication,QHBoxLayout
from PyQt5.QtCore import Qt
from ui_components import ui_components, file_slot
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

        #fileslot = file_slot()
        #setup_file_slot = fileslot.slot_setup()
        #self.tabs.addTab(setup_file_slot ,"radio1")
        #self.slot_arr.append(fileslot)

        
        #fileslot2 = file_slot()
        #setup_file_slot2 = fileslot2.slot_setup()
        #self.tabs.addTab(setup_file_slot2 ,"radio2")
        #self.slot_arr.append(fileslot2)
        

        self.time_progress_slider_setup()
        self.time_stretcher_setup()
        #self.index_controls()

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())