from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget
import sys, os
import numpy as np
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import csv
import datetime
import pandas as pd
import time


cwd = os.getcwd()
if 'portableLIBS' not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'portableLIBS' folder.")
# Rebuild the directory string up to and including 'portablelIBS', prevent import errors
cwd = os.path.sep.join(cwd.split(os.path.sep)[:cwd.split(os.path.sep).index('portableLIBS') + 1])
sys.path.insert(0,cwd)

from software.IbsenSpec.ibsenWidget import Ui_Form

try:
    from software.IbsenSpec.specdriver.spectrometer import (
        GetDLLversion,
        SpectrometersAvailable,
        SPECTROMETER,
        DISB,
        DetectorType,
        Firmware,
        AUX_OUTPUT_MODE,
        TEMPERATURE_FORMAT,
        GAIN_MODE,
        WavelengthCalibration,
        LinearityCalibration,
        Information,
        GPIO_input,
        GPIO_output,
        HW_AVERAGING_STATUS,
        Trigger_mode,
    )
except FileNotFoundError as e:
    print(
        "Error: Could not import specdriver. You might need to install the demo software from Ibsen to rectify this issue."
    )
    print(e)
    # sys.exit(1)


class IbsenWidget(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        if os.getcwd() != os.path.dirname(__file__):
            os.chdir(os.path.dirname(__file__))

        self.spectrometer = None
        self.wavelengths_bounds = []
        self.pixel_bounds = []
        self.wavelengths = np.linspace(190, 435, 4096)
        self.background = np.zeros(len(self.wavelengths))
        self.pixels = np.linspace(0, 4096, 4096)
        self.isSpecConnected = False
        self.st_time = time.time()

        # ---------- Load Spectra from xlsx file ----------
        data = pd.read_excel("Identified_lines_Final.xlsx").values
        self.LIBS_line_names = data[:, 0]
        self.LIBS_line_values = data[:, 1].astype(float)

        # ---------- UI Connections ----------
        self.integrationTimeEntry.returnPressed.connect(self.update_integration_time)
        self.triggerDelayEntry.returnPressed.connect(self.update_trigger_delay)
        self.triggerModeSelectBox.currentTextChanged.connect(
            self.handle_trigger_mode_changed
        )
        self.startAquisitionButton.clicked.connect(self.handle_get_aquisition)
        self.acquireBackgroundButton.clicked.connect(self.acquire_background)

        # Initalize Spectrometer
        try:
            specs = SpectrometersAvailable()
        except:
            print("Error, No spectrometer connected.")
        else:
            if self.init_spectrometer():
                self.isSpecConnected = True
            else:
                print("Error, Spectrometer failed to connect")

        # ------- File Save Initalization -------
        self.setFilePathButton.clicked.connect(self.handle_update_save_path)
        self.saveFileCheck.setEnabled(False)  # Disable the saveFileCheck checkbox
        self.filepath = None

        # ------- Spectra Plot Initialization -------
        onboot_spectrum = 40000 * np.sinc((self.wavelengths - 312.5) / 10) ** 2
        max_intensity, max_index = self.max_value(onboot_spectrum)
        self.maxValueReadout.setText(f"{max_intensity:.2f}")
        self.MaxValueWavelengthReadout.setText(f"{self.wavelengths[max_index]:.2f} nm")
        self.spectraGraph.axes.cla()
        (self.spectraPlot,) = self.spectraGraph.axes.plot(
            self.wavelengths, onboot_spectrum, linewidth=0.5
        )
        self.maxIntensityLocation = self.spectraGraph.axes.scatter(
            self.wavelengths[max_index], max_intensity, c="r", marker="x"
        )

        self.libsLines = [self.spectraGraph.axes.axvline(i, color="r", linestyle="--", linewidth=0.5) for i in self.LIBS_line_values]
        for i in self.libsLines:
            i.set_visible(False)
        self.spectraGraph.axes.set_xlabel("Wavelength [nm]")
        self.spectraGraph.axes.set_ylabel("Intensity [a.u.]")
        self.spectraGraph.axes.set_xlim(self.wavelengths[0], self.wavelengths[-1])
        self.spectraGraph.axes.set_ylim(0, 62000)
        self.spectraGraph.fig.tight_layout()

        # Timer for continuous exposure
        self.graph_update_timer = QTimer()
        self.graph_update_timer.timeout.connect(self.update_graph)
        self.navi_toolbar = NavigationToolbar(self.spectraGraph, self)
        self.spectralayout.insertWidget(0, self.navi_toolbar)

        # timer for ext trig
        self.ext_trig_timer = QTimer()
        self.ext_trig_timer.timeout.connect(self.wait_for_ext_trig)

        self.show()  # Show the GUI

    def init_spectrometer(self):
        try:
            self.spectrometer = SPECTROMETER(0)
            specinfo = self.spectrometer.m_info
            self.spec_status_label.setText("Spectrometer Status: Connected")
            self.pcb_sn_label.setText(f"PCB S/N: {specinfo.DISB_PCB_SerialNumber}")
            self.spec_sn_label.setText(
                f"Spectrometer S/N: {specinfo.Spectrometer_SerialNumber}"
            )
            self.firmware_label.setText(f"Firmware: {specinfo.Firmware}")
            self.spectrometer.AbortCurrentExposure()
            self.spectrometer.SetExposureTime(10.0)
            print(
                f"Spectrometer internal trigger pulse period: {self.spectrometer.GetInternalTriggerPulsePeriod()} ms"
            )
            self.spectrometer.SetRegionOfInterest(190.0, 435.0)
            wl_start, wl_end, pix_start, pix_end = (
                self.spectrometer.GetRegionOfInterest()
            )
            self.wavelengths_bounds = [wl_start, wl_end]
            self.wavelengths = np.array(self.spectrometer.GetWavelengthAxis())
            self.background = np.array(np.zeros(len(self.wavelengths)))
            self.pixel_bounds = [pix_start, pix_end]
            self.spectrometer.SetTriggerMode(
                Trigger_mode(
                    SPI_trigger_enabled=True,
                    ExternalHW_trigger_enabled=True,
                    Internal_trigger_enabled=True,
                )
            )
            self.trig_mode = self.spectrometer.GetTriggerMode()
            if (
                self.trig_mode.SPI_trigger_enabled
                and self.trig_mode.ExternalHW_trigger_enabled
                and self.trig_mode.Internal_trigger_enabled
            ):
                print("\nAll trigger modes have been enabled")

            self.triggerDelayEntry.setText(str(self.spectrometer.GetTriggerDelay()))

        except Exception as E:
            print(E)
            return False
        else:
            return True

    def update_integration_time(self):
        inttime = self.integrationTimeEntry.text()
        if self.isSpecConnected:
            try:
                inttime = float(inttime)
            except ValueError:
                print("Error: Invalid integration time value.")
                self.integrationTimeEntry.setText("Error")
            else:
                self.stop_graph_update_timer()
                # self.spectrometer.AbortCurrentExposure()
                if self.setExposuretime(inttime):
                    print(f"Set integration time to {inttime} ms")
                    self.integrationTimeLabel.setStyleSheet("color: green;")
                    QtCore.QTimer.singleShot(
                        5000, lambda: self.integrationTimeLabel.setStyleSheet("")
                    )

    def setExposuretime(self, time):
        try:
            self.spectrometer.SetExposureTime(time)
        except Exception as e:
            print(e)
            self.integrationTimeEntry.setText("Error")
            return False
        else:
            return True

    def handle_trigger_mode_changed(self):
        mode = self.triggerModeSelectBox.currentText()
        self.set_trigger_mode(mode)

    def set_trigger_mode(self, mode="Continuous"):
        if self.isSpecConnected:
            self.spectrometer.AbortCurrentExposure()

            if mode == "Continuous":
                self.spectrometer.SetTriggerMode(
                    Trigger_mode(
                        ExternalHW_trigger_enabled=False, Internal_trigger_enabled=True
                    )
                )
                self.saveFileCheck.setChecked(
                    False
                )  # Uncheck the saveFileCheck checkbox
            elif mode == "Single":
                self.spectrometer.SetTriggerMode(
                    Trigger_mode(
                        SPI_trigger_enabled=True,
                        ExternalHW_trigger_enabled=False,
                        Internal_trigger_enabled=False,
                    )
                )
            elif mode == "External":
                self.spectrometer.SetTriggerMode(
                    Trigger_mode(
                        ExternalHW_trigger_enabled=True, Internal_trigger_enabled=False
                    )
                )

            self.trig_mode = self.spectrometer.GetTriggerMode()
            print(
                f"SPI: {self.trig_mode.SPI_trigger_enabled}, External HW: {self.trig_mode.ExternalHW_trigger_enabled}, Internal: {self.trig_mode.Internal_trigger_enabled}"
            )
        else:
            print("Error: Spectrometer not connected")

    def handle_get_aquisition(self):
        mode = self.triggerModeSelectBox.currentText()
        if self.isSpecConnected:
            if mode == "Single":
                self.get_single_spectrum()
            elif mode == "Continuous" and not self.graph_update_timer.isActive():
                self.saveFileCheck.setChecked(
                    False
                )  # Uncheck the saveFileCheck checkbox
                self.start_graph_update_timer()
                self.startAquisitionButton.setText("Stop Acquisition")
            elif mode == "Continuous" and self.graph_update_timer.isActive():
                self.stop_graph_update_timer()
                self.startAquisitionButton.setText("Start Acquisition")
            elif mode == "External" and not self.ext_trig_timer.isActive():
                self.ext_trig_timer.start(100)
                self.startAquisitionButton.setText("Stop Acquisition")
            elif mode == "External" and self.ext_trig_timer.isActive():
                self.ext_trig_timer.stop()
                self.startAquisitionButton.setText("Start Acquisition")

        else:
            print("Error: Spectrometer not connected")
            self.startAquisitionButton.setStyleSheet("background-color: red")
            QTimer.singleShot(
                1000, lambda: self.startAquisitionButton.setStyleSheet("")
            )

    def get_single_spectrum(self):
        self.spectrometer.StartExposure()
        # Start listening for a confirmation on data being ready to be read from the image transfer buffer
        while not self.spectrometer.IsDataReady():
            pass
        # When we have exited the above while loop, image data is ready to be transfered
        self.update_graph()

    def acquire_background(self):
        if self.isSpecConnected:
            self.spectrometer.StartExposure()
            # Start listening for a confirmation on data being ready to be read from the image transfer buffer
            while not self.spectrometer.IsDataReady():
                pass
            # When we have exited the above while loop, image data is ready to be transfered
            self.background = np.array(self.spectrometer.ReadSpectrumBuffer())
            self.acquireBackgroundButton.setStyleSheet("background-color: green")
        else:
            self.acquireBackgroundButton.setStyleSheet("background-color: red")
            QTimer.singleShot(
                1000, lambda: self.acquireBackgroundButton.setStyleSheet("")
            )

    def start_graph_update_timer(self):
        self.graph_update_timer.start(50)  # Update every 50 milliseconds
        self.triggerModeSelectBox.setEnabled(
            False
        )  # Disable the trigger mode select box

    def stop_graph_update_timer(self):
        if self.graph_update_timer.isActive():
            self.graph_update_timer.stop()
        self.startAquisitionButton.setText("Start Acquisition")
        self.triggerModeSelectBox.setEnabled(True)  # Enable the trigger mode select box

    def wait_for_ext_trig(self):
        if self.isSpecConnected:
            try:
                def update_graph():
                    if self.spectrometer.IsDataReady():
                        self.update_graph()
                        self.ext_trig_timer.start(100)  # Restart the timer

                self.ext_trig_timer.timeout.connect(update_graph)
                self.ext_trig_timer.start(100)  # Start the timer
            except Exception as e:
                print(e)

    def update_graph(self):
        if self.isSpecConnected:
            do_bkg_subtract = self.subtractBackgroundToggle.value()
            while not self.spectrometer.IsDataReady():
                pass
            spectrum = np.array(self.spectrometer.ReadSpectrumBuffer())
            try:
                self.repratedisplay.setText(f"Refresh Rate: {int(1 / (time.time() - self.st_time))} Hz")
            except:
                pass
            if do_bkg_subtract:
                spectrum = spectrum - self.background

            max_intensity, max_index = self.max_value(spectrum)
            self.maxValueReadout.setText(f"{max_intensity:.2f}")
            self.MaxValueWavelengthReadout.setText(
                f"{self.wavelengths[max_index]:.2f} nm"
            )

            if self.plotSpectralPeakCheck.isChecked():
                self.find_spectral_peaks_LIBS(spectrum)

            else:
                for i in self.libsLines:
                    i.set_visible(False)

            self.spectraPlot.set_ydata(spectrum)

            if self.markMaxCheck.isChecked():
                self.maxIntensityLocation.set_visible(True)
                # self.maxIntensityLocation.set_data(self.wavelengths[max_index], max_intensity)
                # self.maxIntensityLocation = self.spectraGraph.axes.scatter(self.wavelengths[max_index], max_intensity, c='r', marker='x')
                self.maxIntensityLocation.set_offsets(
                    [(self.wavelengths[max_index], max_intensity)]
                )
            else:
                self.maxIntensityLocation.set_visible(False)

            if self.autoscaleY_check.isChecked():
                self.spectraGraph.axes.set_ylim(0, np.max(spectrum) + 500)
            else:
                self.spectraGraph.axes.set_ylim(0, 65536)
            self.spectraGraph.fig.canvas.draw()

            if (self.saveFileCheck.isChecked() and self.triggerModeSelectBox.currentText() != "Continuous"):
                self.save_file(spectrum, bkg=do_bkg_subtract)
            self.spectrometer.ResetSpectrumBuffer()
            self.st_time = time.time()


    def update_trigger_delay(self):
        delay = self.triggerDelayEntry.text()
        if self.isSpecConnected:
            try:
                delay = float(delay)
            except ValueError:
                print("Error: Invalid delay time value.")
                self.triggerDelayEntry.setText("Error")
            else:
                self.spectrometer.SetTriggerDelay(delay)
                if self.spectrometer.GetTriggerDelay() == delay:
                    print(f"Trigger delay set to {delay} ms")
                    self.triggerDelayLabel.setStyleSheet("background-color: green")
                    QTimer.singleShot(
                        5000, lambda: self.triggerDelayLabel.setStyleSheet("")
                    )
                else:
                    print("Error: Invalid delay time value.")
                    self.triggerDelayEntry.setText("Error")

    def handle_update_save_path(self):
        file_dialog = QtWidgets.QFileDialog()
        directory_path = file_dialog.getExistingDirectory(self, "Select Directory")
        if directory_path:
            self.filepath = directory_path
            self.filePathLabel.setText(directory_path)
            self.saveFileCheck.setEnabled(True)  # Enable the saveFileCheck checkbox
        else:
            self.saveFileCheck.setEnabled(False)  # Disable the saveFileCheck checkbox

    def save_file(self, spectra, bkg=0):
        if self.filepath:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]

            if bkg:
                file_name = f"spectra_bkgsub_{timestamp}.csv"
            else:
                file_name = f"spectra_{timestamp}.csv"

            file_path = os.path.join(self.filepath, file_name)
            with open(file_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Wavelength", "Intensity"])
                for wl, intensity in zip(self.wavelengths, spectra):
                    writer.writerow([wl, intensity])

            print(f"File saved: {file_path}")
        else:
            print("Error: Directory not chosen. File not saved.")


    def find_spectral_peaks_LIBS(self, spectrum):
        st = ""
        peak_value, peak_index = self.max_value(spectrum)
        for index, name in enumerate(self.LIBS_line_names):
            intensity = spectrum[np.abs(self.wavelengths - self.LIBS_line_values[index]).argmin()] / peak_value
            if intensity > 0.1:
                self.libsLines[index].set_visible(True)
                wavelength = self.LIBS_line_values[index]
                st += f"{name} ({wavelength:.1f}nm): {intensity:.3f}\n"
            else:
                self.libsLines[index].set_visible(False)
        
        # Split the string into six columns
        lines = st.split("\n")
        num_lines = len(lines)
        col_width = num_lines // 6 + 1
        
        # Create six columns
        cols = [[] for _ in range(6)]
        for i, line in enumerate(lines):
            cols[i % 6].append(line)
        
        # Combine the columns with appropriate spacing
        combined = ""
        for i in range(max(num_lines // 6, num_lines % 6)):
            for col in cols:
                if i < len(col):
                    combined += f"{col[i]:<30}"
                else:
                    combined += " " * 30
            combined += "\n"
        
        self.LineIntensitiesLabel.setText(combined)

    
    def max_value(self, arr):
        max_value = np.max(arr)
        max_index = np.argmax(arr)
        return max_value, max_index


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout
    app = QApplication(sys.argv)

    main_window = QWidget()
    main_window.setWindowTitle("Ibsen Spectrometer UI")
    main_window.resize(1200, 700)  # Set the default window size

    layout = QVBoxLayout(main_window)
    grid_layout = QGridLayout()
    iris_gui = IbsenWidget()
    grid_layout.addWidget(iris_gui, 0, 0)

    layout.addLayout(grid_layout)

    main_window.setLayout(layout)

    main_window.show()

    sys.exit(app.exec_())