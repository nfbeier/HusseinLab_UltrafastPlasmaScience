import sys
import os
import time
import logging
import numpy as np
import h5py  # For saving data
import stellarnet_driver3 as sn
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from PyQt5 import uic

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

class SpectrometerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("spectrometer8.ui", self)

        self.spectrometers = []
        self.wavelengths = []
        self.save_directory = ""  # Default empty, user must select
        self.file_num = 1  # To keep track of saved files

        # Initialize Spectrometers
        for i in range(6):
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
        self.plot_layout = QVBoxLayout(self.plot_graph)
        self.plot_layout.addWidget(self.canvas)

        # Connect buttons
        self.startButton.clicked.connect(self.capture_spectrum)
        self.stopButton.clicked.connect(self.stop_acquisition)
        self.browseButton.clicked.connect(self.browse_directory)  # Button to set save path
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
    def browse_directory(self):
        """Opens a file browser to select a directory for saving spectra."""
        dir_path = QFileDialog.getExistingDirectory(self, "Choose Directory", "./")
        if dir_path:
            self.save_directory = dir_path
            self.SaveData_dir.setText(dir_path)
            logging.info(f"Save directory set to: {dir_path}")

    def capture_spectrum(self):
        """Start spectrum acquisition."""
        # start_time = time.time()
        if self.spectrometers:
            self.set_parameters()
            self.timer.start(500)
        else:
            logging.error("No spectrometer initialized!")
        # end_time = time.time()
        # execution_time = end_time - start_time
        # print(f"Execution time: {execution_time:.6f} seconds")
    def stop_acquisition(self):
        """Stop spectrum acquisition."""
        self.timer.stop()
        logging.info("Spectrum acquisition stopped.")

    def update_plot(self):
        """Acquire and plot spectrum data for all spectrometers."""
        start_time = time.time()
        self.ax.clear()
        colors = ['b', 'g', 'r', 'c', 'm', 'y']

        for i, spectrometer in enumerate(self.spectrometers):
            if spectrometer:
                data = self.get_spectrum(i)
                # print(f"Spectrometer {i} Data:\n", data)  # Debugging print
                # print(f"Wavelengths:\n", self.wavelengths[i])
                # logging.info(f"Spectrometer {i} data shape: {data.shape}")
                self.ax.plot(data[:, 0], data[:, 1], color=colors[i % len(colors)])# self.wavelengths[i]

        self.ax.set_xlabel("Wavelength (nm)")
        self.ax.set_ylabel("Intensity (a.u.)")
        self.ax.set_title("Real-Time Spectrum")
        self.canvas.draw()

        # Save each acquired spectrum
        self.save_spectrum()
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time:.6f} seconds")
    def get_spectrum(self, index):
        """Retrieve spectrum data for a given spectrometer."""
        try:
            return sn.array_spectrum(self.spectrometers[index], self.wavelengths[index])
        except Exception as e:
            logging.error(f"Error retrieving spectrum for Spectrometer {index}: {e}")
            return np.zeros_like(self.wavelengths[index])
    def set_parameters(self):
        """Set parameters for all spectrometers."""
        try:
            int_time = int(self.intTimeInput.text())  # Read integration time input
            for spectrometer in self.spectrometers:
                if spectrometer:
                    spectrometer['device'].set_config(int_time=int_time, scans_to_avg=1, x_smooth=0, x_timing=3)
                    
            logging.info(f"Integration Time set to {int_time} ms.")
        except ValueError:
            logging.error("Invalid parameter value entered!")

    def save_spectrum(self):
        """Save spectrum data for all spectrometers automatically."""
        if not self.save_directory:
            logging.warning("Save directory not set. Spectrum will not be saved.")
            return

        filename = os.path.join(self.save_directory, f"{time.strftime('%Y%m%d')}_LIBS_Spectrum_{self.file_num:05d}.h5")
        self.file_num += 1  # Increment file number

        try:
            with h5py.File(filename, 'w') as hdf:
                for i in range(len(self.spectrometers)):
                    dataset_name = f"StellarNetSpectrum_{i}"
                    data = self.get_spectrum(i)
                    hdf.create_dataset(dataset_name, data=data)
            logging.info(f"Spectrum saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving spectrum: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrometerGUI()
    window.show()
    sys.exit(app.exec_())
