import sys
from PyQt5.QtWidgets import QApplication,QHBoxLayout, QVBoxLayout, QMainWindow, QWidget, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt
from ui_components import ui_components
from spectrogram import spectrogram
from RF_view import RF_view
from traffic_view import Traffic_view
from linked_view import linked_view 


class MainWindow(ui_components,spectrogram,RF_view,Traffic_view,linked_view):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDRagon Vision")

        #===============actual layout stuff===================================

        # Change Window Size
        self.resize(1280, 960)

        self.set_central_widget()

        self.loading_button()

        # View Stacking Layout
        self.view_stack_layout = QVBoxLayout()
        self.view_containers = []

        # Builder Function to add a view with a corresponding button
        def add_stack_row(view_widget, button_text):
            row_container = QWidget()
            row_layout = QHBoxLayout(row_container)

            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(0)

            btn = QPushButton(button_text)
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            btn.setStyleSheet("background-color: #006699; color: #FFC600; font-weight: bold; text-align: center; border: 1px solid #005577")

            btn.clicked.connect(lambda: self.toggle_view_mode(row_container, btn))

            row_layout.addWidget(btn, 1)
            row_layout.addWidget(view_widget, 20)

            self.view_stack_layout.addWidget(row_container, 1)
            self.view_containers.append((row_container, btn))

        # Build the Stacked Views
        traffic_widget = self.traffic_tab()
        add_stack_row(traffic_widget, "T\nR\nA\nF\nF\nI\nC")

        rf_widget = self.RF_view_tab()
        add_stack_row(rf_widget, "R\nA\nD\nI\nO\n\nF\nR\nE\nQ\nU\nE\nN\nC\nY")

        spec_widget = self.spectrogram_tab()
        add_stack_row(spec_widget, "S\nP\nE\nC\nT\nR\nO\nG\nR\nA\nM")

        linked_widget = self.linked_tab()
        add_stack_row(linked_widget, "L\nI\nN\nK\nE\nD\n\nV\nI\nE\nW")

        #threhold adjuster
        self.setup_threshold_incrementor()

        # Create the Main Layout Row
        self.main_content_row = QHBoxLayout()

        # Set up the Sidebar
        self.left_sidebar = QVBoxLayout()
        self.left_sidebar.addLayout(self.dB_incrementer)
        self.left_sidebar.addStretch()

        # Add Everything to the Main Layout
        self.main_content_row.addLayout(self.left_sidebar, 1)
        self.main_content_row.addLayout(self.view_stack_layout, 4)

        # Finalize
        self.layout.addLayout(self.main_content_row)

        # Moved these down so timeline stretcher and index controls are below the views
        self.time_stretcher_setup()
        self.index_controls()
    
    # Method to toggle view mode when user clicks button
    def toggle_view_mode(self, active_container, active_btn):
        # Define the styles
        normal_style = "background-color: #006699; color: #FFC600; font-weight: bold; text-align: center; border: 1px solid #005577"
        active_style = "background-color: #FFC600; color: #006699; font-weight: bold; text-align: center; border: 2px solid #FFC600"

        if active_btn.isChecked():
            # Expand the corresponding view and collapses others
            for container, btn in self.view_containers:
                if container == active_container:
                    container.show()
                    btn.setStyleSheet(active_style)
                else:
                    container.hide()
                    btn.setChecked(False)
                    btn.setStyleSheet(normal_style)
        else:
            # Restore all views to original size
            for container, btn in self.view_containers:
                container.show()
                btn.setStyleSheet(normal_style)
                btn.setChecked(False)

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())