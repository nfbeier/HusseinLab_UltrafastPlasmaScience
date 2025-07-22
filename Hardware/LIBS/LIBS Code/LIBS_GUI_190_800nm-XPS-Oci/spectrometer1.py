import sys
import logging
import numpy as np
import stellarnet_driver3 as sn
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QFileDialog
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5 import uic

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

class SpectrometerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load UI
        uic.loadUi("spectrometer1.ui", self)

        # Initialize Spectrometer
        try:
            self.spectrometer, self.wavelengths = sn.array_get_spec(0)  # First spectrometer
            print(sn.array_get_spec(1))
            logging.info("Spectrometer initialized successfully.")
            # Enable external trigger automatically
            # external_trigger(self.spectrometer, True)
            sn.ext_trig(self.spectrometer,False)
            logging.info("External Trigger Enabled by Default")
        except Exception as e:
            self.spectrometer = None
            self.wavelengths = None
            logging.error(f"Error initializing spectrometer: {e}")

        # Setup Matplotlib figure
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # Add canvas to GUI
        self.plot_layout = QVBoxLayout(self.plot_graph)
        self.plot_layout.addWidget(self.canvas)

        # Connect buttons
        self.startButton.clicked.connect(self.capture_spectrum)
        self.stopButton.clicked.connect(self.save_spectrum)

        # Timer for continuous acquisition
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
    def external_trigger(spectrometer,trigger):
        sn.ext_trig(spectrometer,trigger)
    def set_parameters(self):
        """Set parameters for the spectrometer."""
        try:
            int_time = int(self.intTimeInput.text())
            # sn.set_config(self.spectrometer['device'], int_time=int_time, scans_to_avg=1, x_smooth=0, x_timing=3)
            self.spectrometer['device'].set_config(int_time=int_time, scans_to_avg=1, x_smooth=0, x_timing=3) 
            logging.info(f"Integration Time set to {int_time} ms.")
        except ValueError:
            logging.error("Invalid parameter value entered!")

    def capture_spectrum(self):
        """Start spectrum acquisition."""
        if self.spectrometer:
            self.set_parameters()
            self.timer.start(500)  # Update every 500 ms
           
        else:
            logging.error("Spectrometer not initialized!")

    def update_plot(self):
        """Acquire and plot spectrum data."""
        if self.spectrometer:
            data = self.get_spectrum()
            self.ax.clear()
            self.ax.plot(self.wavelengths, data, label="Spectrum", color="b")
            self.ax.set_xlabel("Wavelength (nm)")
            self.ax.set_ylabel("Intensity (a.u.)")
            self.ax.set_title("Real-Time Spectrum")
            self.ax.legend()
            self.canvas.draw()
        else:
            logging.error("No spectrometer detected!")

    def get_spectrum(self):
        """Retrieve spectrum data."""
        try:
            return sn.array_spectrum(self.spectrometer, self.wavelengths)
        except Exception as e:
            logging.error(f"Error retrieving spectrum: {e}")
            return np.zeros_like(self.wavelengths)

    def save_spectrum(self):
        """Save spectrum data to a CSV file."""
        if self.spectrometer:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Spectrum", "", "CSV Files (*.csv)")
            if filename:
                with open(filename, "w") as file:
                    file.write("Wavelength (nm), Intensity\n")
                    data = self.get_spectrum()
                    for w, d in zip(self.wavelengths, data):
                        file.write(f"{w},{d}\n")
                logging.info(f"Spectrum saved to {filename}")
        else:
            logging.error("No spectrometer data to save!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrometerGUI()
    window.show()
    sys.exit(app.exec_())
