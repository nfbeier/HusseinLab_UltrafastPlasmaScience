import sys
import logging
import numpy as np
import stellarnet_driver3 as sn
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QFileDialog, QCheckBox
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5 import uic

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

class SpectrometerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load UI
        uic.loadUi("spectrometer6.ui", self)

        # Initialize Spectrometers (0 to 5)
        self.spectrometers = []
        self.wavelengths = []
        
        for i in range(6):  # Support up to 6 spectrometers
            try:
                spectrometer, wavelengths = sn.array_get_spec(i)
                self.spectrometers.append(spectrometer)
                self.wavelengths.append(wavelengths)
                
                logging.info(f"Spectrometer {i} initialized successfully.")
            except Exception as e:
                logging.error(f"Error initializing spectrometer {i}: {e}")

        # Setup Matplotlib figure
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        # Add canvas to GUI
        self.plot_layout = QVBoxLayout(self.plot_graph)
        self.plot_layout.addWidget(self.canvas)

        # Connect buttons
        self.startButton.clicked.connect(self.capture_spectrum)
        self.stopButton.clicked.connect(self.save_spectrum)

        # Connect external trigger checkbox
        self.extTriggerCheckBox.stateChanged.connect(self.toggle_external_trigger)

        # Timer for continuous acquisition
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)

    def toggle_external_trigger(self):
        """Enable or disable external trigger based on user selection."""
        trigger_enabled = self.extTriggerCheckBox.isChecked()  # Check if the checkbox is selected
        
        for spectrometer in self.spectrometers:
            if spectrometer:
                try:
                    sn.ext_trig(spectrometer, trigger_enabled)
                    logging.info(f"External Trigger {'Enabled' if trigger_enabled else 'Disabled'}")
                except Exception as e:
                    logging.error(f"Error setting external trigger: {e}")

    def set_parameters(self):
        """Set parameters for all spectrometers."""
        try:
            int_time = int(self.intTimeInput.text())
            for spectrometer in self.spectrometers:
                if spectrometer:
                    spectrometer['device'].set_config(int_time=int_time, scans_to_avg=1, x_smooth=0, x_timing=3)
            logging.info(f"Integration Time set to {int_time} ms.")
        except ValueError:
            logging.error("Invalid parameter value entered!")

    def capture_spectrum(self):
        """Start spectrum acquisition for all spectrometers."""
        if self.spectrometers:
            self.set_parameters()
            self.timer.start(10)  # Update every 500 ms
        else:
            logging.error("No spectrometer initialized!")

    def update_plot(self):
        """Acquire and plot spectrum data for all spectrometers."""
        self.ax.clear()
        colors = ['b', 'g', 'r', 'c', 'm', 'y']  # Colors for up to 6 spectrometers

        for i, spectrometer in enumerate(self.spectrometers):
            if spectrometer:
                data = self.get_spectrum(i)
                self.ax.plot(self.wavelengths[i], data,  color=colors[i % len(colors)]) #label=f"Spectrometer {i}"

        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity (a.u.)")
        self.ax.set_title("Real-Time Spectrum")
        # self.ax.legend()
        self.canvas.draw()

    def get_spectrum(self, index):
        """Retrieve spectrum data for a given spectrometer."""
        try:
            return sn.array_spectrum(self.spectrometers[index], self.wavelengths[index])
        except Exception as e:
            logging.error(f"Error retrieving spectrum for Spectrometer {index}: {e}")
            return np.zeros_like(self.wavelengths[index])

    def save_spectrum(self):
        """Save spectrum data for all spectrometers to a CSV file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Spectrum", "", "CSV Files (*.csv)")
        if filename:
            with open(filename, "w") as file:
                file.write("Wavelength (nm), ")
                file.write(", ".join([f"Spectrometer {i} Intensity" for i in range(len(self.spectrometers))]) + "\n")

                for j in range(len(self.wavelengths[0])):  # Assuming all spectrometers have the same wavelength range
                    row = [str(self.wavelengths[0][j])]  # Wavelength
                    for i in range(len(self.spectrometers)):
                        data = self.get_spectrum(i)
                        row.append(str(data[j]))
                    file.write(", ".join(row) + "\n")

            logging.info(f"Spectrum saved to {filename}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrometerGUI()
    window.show()
    sys.exit(app.exec_())
