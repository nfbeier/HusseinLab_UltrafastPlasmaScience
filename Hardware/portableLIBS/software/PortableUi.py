from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
import sys, os
import numpy as np
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pyqtgraph as pg
import csv
import datetime
import numpy as np
import pandas as pd
import time
import joblib
# import sklearn
cwd = os.getcwd()
if 'portableLIBS' not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'portableLIBS' folder.")
# Rebuild the directory string up to and including 'portablelIBS', prevent import errors
cwd = os.path.sep.join(cwd.split(os.path.sep)[:cwd.split(os.path.sep).index('portableLIBS') + 1])
os.chdir(cwd)
cwd = os.path.join(cwd, 'software') 

sys.path.insert(0,cwd)

from Viron.Viron import VironLaser
from Viron.telnetGUI import TelnetSessionGUI
from PortableUI_window import Ui_MainWindow
import h5py
import threading
try:
    from IbsenSpec.specdriver.spectrometer import (
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

# defaults for plots
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("PortableUI")
        self.shotnum = 1

        self.is_viron_connected = False
        self.closeEvent = self.on_close
        self.handle_button_connections()

        self._init_viron()
        self._init_ibsen()

        
    def handle_button_connections(self):
        # connect button
        self.viron_connect_button.clicked.connect(self.handle_connect_to_laser)
        # standby button
        self.viron_standby_button.clicked.connect(self.toggle_standby)
        # auto fire button
        self.viron_autofire_button.clicked.connect(self.toggle_autofire)
        # single shot button
        self.viron_singlefire_button.clicked.connect(self.toggle_singlefire)
        # burst fire button
        self.viron_burst_fire_button.clicked.connect(self.toggle_burst_fire)
        # set rep rate
        self.viron_set_reprate_button.clicked.connect(self.handle_set_rep_rate)
        # set qs delay
        self.viron_set_qsdelay_button.clicked.connect(self.handle_set_qs_delay)

        self.viron_set_burst_button.clicked.connect(self.handle_set_bst_num)

        # init statuses
        self.laser_simple_status = {"isReady" : 'Disconnected'}
        self.handle_get_status(status_hex="0x000000000000")

        # ---------- Ibsen UI Connections ----------
        self.integrationTimeEntry.returnPressed.connect(self.update_integration_time)
        self.triggerDelayEntry.returnPressed.connect(self.update_trigger_delay)
        self.detectionThresholdEntry.returnPressed.connect(self.update_detection_threshold)
        self.triggerModeSelectBox.currentTextChanged.connect(
            self.handle_trigger_mode_changed
        )
        self.startAquisitionButton.clicked.connect(self.handle_get_aquisition)
        # self.acquireBackgroundButton.clicked.connect(self.acquire_background)
        # ------- File Save Initalization -------
        self.setFilePathButton.clicked.connect(self.handle_update_save_path)
        self.saveFileCheck.setEnabled(False)  # Disable the saveFileCheck checkbox
        self.filepath = None

        # ML model loading
        self.actionSet_ML_File.triggered.connect(self.handle_load_ml_model)

        # energy calculator stuff
        self.qsdelaycalc_entry.textChanged.connect(self.update_qsdelay_calculator)
        self.energycalc_entry.textChanged.connect(self.update_energy_calculator)



    def _init_viron(self):
        self.host = self.host_entry.text()
        self.port = self.port_entry.text()
        self.password = self.password_entry.text()
        try:
            self.tngui = TelnetSessionGUI()
            self.laser = VironLaser(self.host, self.port, self.password, telnetgui=self.tngui)
            self.tngui.set_laser(self.laser)
        except:
            print("failure initalizing Viron")
            return False

        else:
            self.is_viron_connected = False
            self.currentstate = None
            self.interlock_triggered = False
            self.states = ['standby', 'stop', 'fire', 'single_shot']
            self.tngui_box.addWidget(self.tngui)
            self.bstnum = 1
            self.viron_burst_entry.setText(str(self.bstnum))
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.handle_get_status)
            self.status_timer.setInterval(500)
            return True
            
    def handle_get_status(self, status_hex=None):
        """
        Handles the action when the "Get Status" button is clicked.
        Retrieves the laser status hex value and parses it into a status dictionary.
        Then, it displays the status on the GUI.

        Returns:
            None
        """
        if status_hex is None:
            if self.is_viron_connected:
                self._get_values()                      
                status_hex = self.laser.get_status()    
                temps = self.laser.get_temps()

            else:
                return
            threading.Thread(target=self._get_status_values, args=(status_hex, temps,)).start()

    def handle_set_bst_num(self):
        bstnum = self.viron_burst_entry.text()

        if bstnum.isdigit() and 0 < int(bstnum) < 61:
            result = self.laser.send_command(f"$BSTON {bstnum}")
            if result:
                print(f"Set burst to {bstnum}")
                self.bstnum = int(bstnum)
        else:
            QMessageBox.warning(self, "Invalid Input", "Insvalid burst number. Please enter an integer between 1 and 60.")
            return False
        
    def _get_status_values(self, status_hex, temps):
         if status_hex is not None:   
            status = self._parse_status(status_hex)
            self.display_status(status)
            self.display_critical_info(status, temps)
            if status['System Interlock Laser Node'] == "Fault" and self.currentstate != 'stop':
                self.interlock_triggered = True
                self.toggle_stop()
            elif status['System Interlock Laser Node'] == "OK" and self.interlock_triggered:
                self.toggle_standby()
 

    def _get_values(self):
        try:
            qs_delay = self.laser.send_command('$QSDELAY ?', response=True).split()[1]
            # qs_pre = self.laser.send_command('$QSPRE ?', response=True).split()[1]
            reprate = self.laser.send_command('$DFREQ ?', response=True).split()[1]
        except:
            return False
        qs_delay_entry_text = self.viron_qsdelay_entry.text()
        # qs_pre_entry_text = self.viron_qspre_entry.text()
        reprate_entry_text = self.viron_reprate_entry.text()

        if str(qs_delay) != qs_delay_entry_text:
            if qs_delay_entry_text == '':
                self.viron_qsdelay_entry.setText(str(qs_delay))
            else:
                self.handle_set_qs_delay()

        # if str(qs_pre) != qs_pre_entry_text:
        #     if qs_pre_entry_text == "":
        #         self.viron_qspre_entry.setText(str(qs_pre))
        #     else:
        #         self.handle_set_qs_pre()

        if str(reprate) != reprate_entry_text:
            if reprate_entry_text == "":
                self.viron_reprate_entry.setText(str(reprate)) 
            else:
                self.handle_set_rep_rate()

    def _parse_status(self, hex_value):
        """
        Parses the status hex value into a dictionary containing the status information.
        
        input:
        - hex_value (str): The status hex value.
        
        return:
        - status (dict): The status dictionary containing key-value pairs.
        """
        
        
        # Convert hex value to binary string
        binary_string = bin(int(hex_value, 16))[2:].zfill(48)

        # Extract individual status based on byte and bit positions
        self.status = {}

        # Byte 1
        self.status['Fire Mode'] = 'Disabled' if binary_string[0] == '0' else 'Fire'
        self.status['Standby Mode'] = 'Stop' if binary_string[1] == '0' else 'Standby'
        self.status['Diode Trigger Mode'] = 'Internal' if binary_string[2] == '0' else 'External'
        self.status['Q-Switch Mode'] = 'Internal' if binary_string[3] == '0' else 'External'
        self.status['Divide By Mode'] = 'Normal' if binary_string[4] == '0' else 'Divide By'
        self.status['Burst Mode'] = 'Continuous' if binary_string[5] == '0' else 'Burst'
        self.status['Q-Switch'] = 'Disabled' if binary_string[6] == '0' else 'Enabled'
        self.status['Ready'] = "Ready" if binary_string[7] == '0' else 'Not Ready'

        # Byte 2
        self.status['UV Illumination'] = 'Disabled' if binary_string[8] == '0' else 'Enabled'
        self.status['Remote Q-Switch'] = 'Normal Q-Switch' if binary_string[9] == '0' else 'Q-Switch off'
        self.status['50 Ohm Trigger Termination'] = 'Disabled' if binary_string[10] == '0' else 'Enabled'
        self.status['BLE Session Temp'] = 'No Session' if binary_string[11] == '0' else 'Session'
        self.status['Diode TEC Running Temp'] = 'Off' if binary_string[12] == '0' else 'Runnng'
        self.status['LAN Session Temp'] = 'No Session' if binary_string[13] == '0' else 'Session'
        self.status['NLO Oven 2 Running Temp'] = 'Off' if binary_string[14] == '0' else 'Running'
        self.status['NLO Oven 1 Running Temp'] = 'Off' if binary_string[15] == '0' else 'Running'

        # Byte 3
        self.status['Remote Interlock Laser'] = 'No' if binary_string[16] == '0' else 'Yes'
        self.status['Laser Temperature Range'] = 'OK' if binary_string[17] == '0' else 'Fault'
        self.status['Charge Fault'] = 'OK' if binary_string[18] == '0' else 'Fault'
        self.status['Diode Current Fault'] = 'OK' if binary_string[19] == '0' else 'Fault'
        self.status['Diode Temperature High or Low'] = 'OK' if binary_string[20] == '0' else 'Fault'
        self.status['Diode Temperature Control Fault'] = 'OK' if binary_string[21] == '0' else 'Fault'
        self.status['System Interlock System/TEC Temp/Sys OK'] = 'OK' if binary_string[22] == '0' else 'Fault'
        self.status['System Interlock Laser Node'] = 'OK' if binary_string[23] == '0' else 'Fault'

        # Byte 4
        self.status['Reserved for BLE'] = 'No Action' if binary_string[24] == '0' else 'No Action'
        self.status['Reserved'] = 'No Action' if binary_string[25] == '0' else 'No Action'
        self.status['Operations Config Checksum'] = 'OK' if binary_string[26] == '0' else 'Fault'
        self.status['Factory Config Checksum'] = 'Ok' if binary_string[27] == '0' else 'Fault'
        self.status['CAN bus fault'] = 'OK' if binary_string[28] == '0' else 'Fault'
        self.status['Run time fault'] = 'OK' if binary_string[29] == '0' else 'Fault'
        self.status['RAM test fault'] = 'OK' if binary_string[30] == '0' else 'Fault'
        self.status['Watchdog Timeout'] = 'OK' if binary_string[31] == '0' else 'Fault'

        # Byte 5
        self.status['External Lamp PRF'] = 'OK' if binary_string[32] == '0' else 'PRF High'
        self.status['Laser Temperature Warning'] = 'OK' if binary_string[33] == '0' else 'Warning'
        self.status['Pre-Lase Detect/Q-Switch inhibited'] = 'OK' if binary_string[34] == '0' else 'Inhibited'
        self.status['CAN Bus Illegal ID or data'] = 'No' if binary_string[35] == '0' else 'Yes'
        self.status['CAN Bus Overrun'] = 'No' if binary_string[36] == '0' else 'Yes'
        self.status['Diode Current Limit'] = 'OK' if binary_string[37] == '0' else 'Warning'
        self.status['Reserved for Log Only - Temp Laser'] = 'Temp' if binary_string[38] == '0' else 'Laser'
        self.status['Diode/TEC Temp. Warning'] = 'OK' if binary_string[39] == '0' else 'Warning'

        # Byte 6
        self.status['NLO Oven 2 out of tolerance'] = 'No' if binary_string[40] == '0' else 'Yes'
        self.status['NLO Oven 2 timeout, oven 2 off'] = 'OK' if binary_string[41] == '0' else 'Warning'
        self.status['NLO Oven 2 over temp, oven 2 off'] = 'OK' if binary_string[42] == '0' else 'Warning'
        self.status['NLO Oven 2 open sensor, oven 2 off'] = 'OK' if binary_string[43] == '0' else 'Warning'
        self.status['NLO Oven 1 out of tolerance'] = 'No' if binary_string[44] == '0' else 'Yes'
        self.status['NLO Oven 1 timeout, oven 1 off'] = 'OK' if binary_string[45] == '0' else 'Warning'
        self.status['NLO Oven 1 over temp, oven 1 off'] = 'OK' if binary_string[46] == '0' else 'Warning'
        self.status['NLO Oven 1 open sensor, oven 1 off'] = 'OK' if binary_string[47] == '0' else 'Warning'


        # warming / rtf / fault

        if binary_string[23] == '1':
            self.laser_simple_status['isReady'] = 'Interlock Fault'
        elif binary_string[16:47] == str('0'*23 + '10000100') or binary_string[16:47] == str('0'*23 + '00000100'):
            if not self.currentstate:
                self.laser_simple_status['isReady'] = 'Idle'
            else:
                self.laser_simple_status['isReady'] = 'Warming'
        elif binary_string[16:47] == str('0'*31):
            self.laser_simple_status['isReady'] = 'Ready'      
        else:
            self.laser_simple_status['isReady'] = 'Fault'  
        return self.status 

    def display_critical_info(self, status, temps):
        """
        Displays the critical status information on the GUI.
        
        Input:
        - status (dict): The status dictionary containing key-value pairs.
        """
        status_text = "Modes:\n"
        status_text += f"  Fire Mode: {status['Fire Mode']}\n"
        status_text += f"  Standby Mode: {status['Standby Mode']}\n"
        status_text += f"  Status: {status['Ready']}\n"
        status_text += f"  Q-Switch: {status['Q-Switch']}\n"
        status_text += "Interlocks:\n"
        status_text += f"  Remote interlock: {status['Remote Interlock Laser']}\n"
        status_text += f"  System Interlock: {status['System Interlock System/TEC Temp/Sys OK']}\n"
        status_text += f"  Laser Node Interlock: {status['System Interlock Laser Node']}\n"
        if self.is_viron_connected:
            status_text += "Temperatures:\n"
            status_text += f"  Laser Temp: {temps['Laser Temp']} C\n"
            status_text += f"  Diode Temp: {temps['Diode Temp']} C\n"
        self.critical_status_label.setText(status_text)

        if self.laser_simple_status['isReady'] == 'Interlock Fault':
            self.laser_status_label.setStyleSheet("color: red")
        elif self.laser_simple_status['isReady'] == 'Warming':
            self.laser_status_label.setStyleSheet("color: orange")
        elif self.laser_simple_status['isReady'] == 'Ready':
            self.laser_status_label.setStyleSheet("color: green")
        else:
            self.laser_status_label.setStyleSheet("color: black")

        self.laser_status_label.setText(self.laser_simple_status['isReady'])
         
    def display_status(self, status):
        # Define the headers for each bundle of 8 lines
        headers = ["Status Byte 1", "Status Byte 2", "Fault Byte 1", "Fault Byte 2", "Warning Byte 1", "Warning Byte 2"]

        # ToDo: Color code status based on fault/warning
        status_text_1 = ""
        status_text_2 = ""
        i = 0
        j = 0
        for key, value in status.items():
            if i % 8 == 0:
                # Add the header for the current bundle of 8 lines
                header_index = i // 8
                if j > 2:
                    status_text_2 += f"\n{headers[header_index]}:\n"
                else:
                    status_text_1 += f"\n{headers[header_index]}:\n"
                j += 1
            if j > 3:
                status_text_2 += f"  {key}: {value}\n"
            else:
                status_text_1 += f"  {key}: {value}\n"
            i += 1

        self.status_label_left.setText(status_text_1)
        self.status_label_right.setText(status_text_2)
        
    def handle_connect_to_laser(self):
        """
        Handles the action when the "Connect" button is clicked.
        Attempts to connect to the laser using the provided host, port, and password.
        Updates the GUI with the connection status.

        Returns:
            None
        """
        if self.laser.connect_to_laser():
            self.viron_connect_button.setStyleSheet("background-color: green")
            self.status_timer.start()
            self.is_viron_connected = True

        else:
            self.viron_connect_button.setStyleSheet("background-color: red")
            self.is_viron_connected = False

    def toggle_standby(self):
        """
        Handles the action when the "Standby" button is clicked.
        Sets the laser in standby mode and updates the GUI accordingly.

        Returns:
            None
        """
        if self.currentstate == 'standby':
            return True
        if self.laser.set_standby():
            self.interlock_triggered = False
            self.currentstate = 'standby'
            self.viron_autofire_button.setChecked(False)
            self.viron_singlefire_button.setChecked(False)
            self.viron_singlefire_button.setStyleSheet("background-color : lightgrey")
            self.viron_standby_button.setStyleSheet("background-color : green")
            self.viron_autofire_button.setStyleSheet("background-color : lightgrey")
            self.viron_burst_fire_button.setStyleSheet("background-color : lightgrey")
            self.viron_singlefire_button.setEnabled(True)
            self.viron_burst_fire_button.setEnabled(True)
            self.viron_autofire_button.setEnabled(True)
            if not self.status_timer.isActive():
                self.status_timer.start()
            return True
        print("Failed to set laser to standby")
        return False

    def toggle_stop(self):
        """
        Handles the action when the "Stop" button is clicked.
        Sets the laser in stop mode and updates the GUI accordingly.

        Returns:
            None
        """
        if self.currentstate == 'stop':
            return True
        
        if self.laser.set_stop():
            self.currentstate = 'stop'
            self.viron_standby_button.setChecked(False)
            self.viron_autofire_button.setChecked(False)
            self.viron_singlefire_button.setChecked(False)
            self.viron_singlefire_button.setStyleSheet("background-color : lightgrey")
            self.viron_standby_button.setStyleSheet("background-color : orange")
            self.viron_autofire_button.setStyleSheet("background-color : lightgrey")
            self.viron_burst_fire_button.setStyleSheet("background-color : lightgrey")
            if not self.status_timer.isActive():
                self.status_timer.start()

            return True
        else:
            print("failed to set stop")
            return False

    def toggle_autofire(self):
        """
        Handles the action when the "Fire Placeholder" button is clicked.
        Sets the laser in fire mode and updates the GUI accordingly.

        Returns:
            None
        """
        if not self.laser.set_standby():
            print("failed to set standby")
            return False
        if self.currentstate != 'fire':
            # set to internal trigger
            self.laser.set_auto_fire()
            print("Auto Fire Set")
            self.currentstate = 'fire'
            
        if self.laser.set_fire():
            self.currentstate = 'fire'
            # if self.status_timer.isActive():
            #     self.status_timer.stop()
        else:
            print("failed to set fire")
            return
        
        self.viron_standby_button.setChecked(False)
        self.viron_singlefire_button.setChecked(False)

        self.viron_singlefire_button.setStyleSheet("background-color : lightgrey")
        self.viron_standby_button.setStyleSheet("background-color : lightgrey")
        self.viron_autofire_button.setStyleSheet("background-color : red")
        self.viron_burst_fire_button.setStyleSheet("background-color : lightgrey")
        self.viron_singlefire_button.setEnabled(False)
        self.viron_burst_fire_button.setEnabled(False)

    def toggle_singlefire(self):
        """
        Handles the action when the "Set Single Shot" button is clicked.
        Sets the laser in single shot mode and updates the GUI accordingly.

        Returns:
            None
        """
        if not self.laser.send_command("$STANDBY"):
            print("Failed to set standby")
            return False
        if self.currentstate != 'single_shot':
            if self.laser.set_single_shot():
                self.currentstate = 'single_shot'
            else:
                print("Single Shot Not Set")
                return

            self.viron_standby_button.setChecked(False)
            self.viron_autofire_button.setChecked(False)
            
            self.viron_standby_button.setStyleSheet("background-color : lightgrey")
            self.viron_autofire_button.setStyleSheet("background-color : lightgrey")
            self.viron_singlefire_button.setStyleSheet("background-color : red")
            self.viron_burst_fire_button.setStyleSheet("background-color : lightgrey")
            self.viron_autofire_button.setEnabled(False)
            self.viron_burst_fire_button.setEnabled(False)

        if self.laser.fire_single_shot():
            print("firin mah lazor")  
            
    def toggle_burst_fire(self):
        if not self.laser.send_command("$STANDBY"):
            return False
        if self.currentstate != 'burst':
            if self.laser.set_burst_mode(self.bstnum):
                self.viron_burst_fire_button.setStyleSheet("background-color : red")
                self.viron_standby_button.setStyleSheet("background-color : lightgrey")
                self.viron_autofire_button.setStyleSheet("background-color : lightgrey")  
                self.viron_singlefire_button.setStyleSheet("background-color : lightgrey")
                self.viron_autofire_button.setEnabled(False)
                self.viron_singlefire_button.setEnabled(False)
            else:
                return False
            self.currentstate = 'burst'
        self.handle_set_bst_num()
        if self.laser.set_fire():
            print("Pew Pew ima firin multiple lazors")
        else:
            return False
        return True    
               
    def handle_set_rep_rate(self):
        """
        Handles the action when the "Set Rep Rate" button is clicked.
        Retrieves the repetition rate value from the text entry and sets it on the laser.

        Returns:
            None
        """
        rate = self.viron_reprate_entry.text()
        if rate.isdigit():
            self.laser.set_rep_rate(int(rate))
            
    def handle_set_qs_delay(self):
        '''
        Handles the action when the "Set Q-Switch Delay" button is clicked.
        '''
        delay = self.viron_qsdelay_entry.text()
        if delay.isdigit():
            if self.laser.set_qs_delay(int(delay)):
                print('Q-Switch Delay Set to ', delay)
                return True
        return False
    
    # def handle_set_qs_pre(self):
    #     '''
    #     Handles the action when the "Set Q-Switch pre" button is clicked.
    #     '''
    #     delay = self.viron_qspre_entry.text()
    #     if delay.isdigit():
    #         if self.laser.set_qs_pre(int(delay)):
    #             print('Q-Switch Pre Set to ', delay)
    #             return True
    #     return False   

    def _init_ibsen(self):
        """
        Initializes the Ibsen spectrometer and sets up the necessary variables and plots.

        This method performs the following tasks:
        - Initializes the Ibsen spectrometer.
        - Loads spectra from an xlsx file.
        - Sets up the necessary variables for plotting.
        - Sets up the initial plot of the spectra.

        Returns:
            None
        """
        self.spectrometer = None
        self.wavelengths_bounds = []
        self.pixel_bounds = []
        self.detectionThresholdEntry.setText("0.25")
        self.detectionThreshold = 0.25
        self.wavelengths = np.linspace(190, 435, 4096)
        self.background = np.zeros(len(self.wavelengths))
        self.pixels = np.linspace(0, 4096, 4096)
        self.isSpecConnected = False
        self.st_time = time.time()

        # ---------- Load Spectra from xlsx file ----------
        data = pd.read_excel(r"software/IbsenSpec/Identified_lines_Final.xlsx").values
        self.LIBS_line_names = data[:, 0]
        self.LIBS_line_values = data[:, 1].astype(float)

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
        
        self.pen = pg.mkPen('k', width=0.5)
        # set up spectrometer widgets
        self.spectraGraph.setBackground('w')
        self.spectraGraph.setLabel("bottom", "Wavelength [nm]")
        self.spectraGraph.setLabel("left", "Intensity [a.u.]")

        # init spectral plot
        onboot_spectrum = 40000 * np.sinc((self.wavelengths - (312.5)) / 50) ** 2
        self.spectraGraph.plot(self.wavelengths, onboot_spectrum, pen=self.pen)
        self.spectraGraph.setXRange(self.wavelengths[0], self.wavelengths[-1])
        self.spectraGraph.setYRange(0, 65535)
        
        max_intensity, max_index = self.max_value(onboot_spectrum)
        self.maxIntensityLocation = pg.ScatterPlotItem(
            [self.wavelengths[max_index]], [max_intensity], symbol='x', pen='r', brush='r'
        )
        self.spectraGraph.addItem(self.maxIntensityLocation)

        # self.libsLines = [self.spectraGraph.axes.axvline(i, color="r", linestyle="--", linewidth=0.5) for i in self.LIBS_line_values]
        # for i in self.libsLines:
        #     i.set_visible(False)


        # Timer for continuous exposure
        self.graph_update_timer = QTimer()
        self.graph_update_timer.timeout.connect(self.update_graph)


        # timer for ext trig
        self.ext_trig_timer = QTimer()
        self.ext_trig_timer.timeout.connect(self.wait_for_ext_trig)

    def init_spectrometer(self):
        """
        Initializes the spectrometer by connecting to it, setting various parameters,
        and retrieving information about the spectrometer.

        Returns:
            bool: True if the spectrometer is successfully initialized, False otherwise.
        """
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
            self.spectrometer.SetInternalTriggerPulsePeriod(16.6) # 16.6 ms = 60 Hz
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
        
    def update_detection_threshold(self):
        """
        Updates the detection threshold based on the value entered in the detectionThresholdEntry field.
        If the value is invalid (not a float between 0 and 1), a warning message is displayed and the default value of 0.1 is set.
        If the value is valid, it is stored in the detectionThreshold variable and the detectionThresholdLabel is updated accordingly.
        The detectionThresholdLabel color is set to green for 5 seconds to indicate a successful update.
        """
        threshold = self.detectionThresholdEntry.text()
        if self.isSpecConnected:
            try:
                threshold = float(threshold)
                if threshold > 1 or threshold < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Value", "Please enter a value between 0 and 1 for the detection threshold.")
                self.detectionThresholdEntry.setText("0.1")
            else:
                self.detectionThreshold = threshold
                self.detectionThresholdLabel.setStyleSheet("color: green;")
                QTimer.singleShot(
                    5000, lambda: self.detectionThresholdLabel.setStyleSheet("")
                )


    def update_integration_time(self):
        """
        Updates the integration time for the spectrometer.

        This method retrieves the integration time value from the integrationTimeEntry widget,
        converts it to a float, and sets it as the new integration time for the spectrometer.
        If the integration time value is invalid, an error message is displayed and the integrationTimeEntry
        widget is set to "Error". The method also stops the graph update timer and the external trigger timer,
        aborts the current exposure, and sets the new integration time if it is valid. Finally, it updates the
        integrationTimeLabel to indicate the new integration time and changes the background color of the
        startAquisitionButton to red for 1 second.

        Returns:
            None
        """        
        inttime = self.integrationTimeEntry.text()
        if self.isSpecConnected:
            try:
                inttime = float(inttime)
            except ValueError:
                print("Error: Invalid integration time value.")
                self.integrationTimeEntry.setText("Error")
            else:
                self.stop_graph_update_timer()
                if self.ext_trig_timer.isActive():
                    self.ext_trig_timer.stop()

                self.spectrometer.AbortCurrentExposure()
                self.handle_trigger_mode_changed()
                if self.setExposuretime(inttime):
                    print(f"Set integration time to {inttime} ms")
                    self.integrationTimeLabel.setStyleSheet("color: green;")
                    QtCore.QTimer.singleShot(
                        5000, lambda: self.integrationTimeLabel.setStyleSheet("")
                    )
                    self.startAquisitionButton.setStyleSheet("background-color: red")
                    QtCore.QTimer.singleShot(1000, lambda: self.startAquisitionButton.setStyleSheet("")) 

    def setExposuretime(self, time):
        """
        Sets the exposure time for the spectrometer.

        Args:
            time (float): The exposure time in seconds.

        Returns:
            bool: True if the exposure time was set successfully, False otherwise.
        """
        try:
            self.spectrometer.SetExposureTime(time)
        except Exception as e:
            print(e)
            self.integrationTimeEntry.setText("Error")
            return False
        else:
            return True

    def handle_trigger_mode_changed(self):
        """
        Handles the event when the trigger mode is changed.
        
        Retrieves the selected trigger mode from the triggerModeSelectBox and calls the
        set_trigger_mode method with the selected mode as the argument.
        """
        mode = self.triggerModeSelectBox.currentText()
        self.set_trigger_mode(mode)

    def set_trigger_mode(self, mode="Continuous"):
        """
        Sets the trigger mode for the spectrometer.

        Args:
            mode (str): The trigger mode to set. Valid options are "Continuous", "Single", or "External". Defaults to "Continuous".

        Returns:
            None

        Raises:
            None
        """
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
        """
        Handles the acquisition process based on the selected trigger mode.

        This method resets the spectrum buffer, retrieves the selected trigger mode,
        and performs the corresponding actions based on the mode. It starts or stops
        the acquisition process, updates the graph, and handles external triggering.

        Returns:
            None
        """
        self.spectrometer.ResetSpectrumBuffer()
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
                self.ext_trig_timer.start(10)
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
        """
        Retrieves a single spectrum from the spectrometer.

        This method starts the exposure, waits for the data to be ready, and then updates the graph with the retrieved spectrum.

        Returns:
            None
        """
        self.spectrometer.StartExposure()
        # Start listening for a confirmation on data being ready to be read from the image transfer buffer
        while not self.spectrometer.IsDataReady():
            pass
        # When we have exited the above while loop, image data is ready to be transfered
        self.update_graph()

    # def acquire_background(self):
    #     """
    #     Acquires the background spectrum from the spectrometer.

    #     If the spectrometer is connected, it starts the exposure and waits for the data to be ready.
    #     Once the data is ready, it reads the spectrum buffer and stores it as the background spectrum.
    #     If the spectrometer is not connected, it sets the background acquisition button color to red temporarily.

    #     Args:
    #         None

    #     Returns:
    #         None
    #     """
    #     if self.isSpecConnected:
    #         self.spectrometer.StartExposure()
    #         # Start listening for a confirmation on data being ready to be read from the image transfer buffer
    #         while not self.spectrometer.IsDataReady():
    #             pass
    #         # When we have exited the above while loop, image data is ready to be transfered
    #         self.background = np.array(self.spectrometer.ReadSpectrumBuffer())
    #         self.acquireBackgroundButton.setStyleSheet("background-color: green")
    #     else:
    #         self.acquireBackgroundButton.setStyleSheet("background-color: red")
    #         QTimer.singleShot(
    #             1000, lambda: self.acquireBackgroundButton.setStyleSheet("")
    #         )

    def start_graph_update_timer(self):
        """
        Starts the graph update timer.

        This method starts a timer that triggers the update of the graph at regular intervals.
        The graph is updated every 1 millisecond.

        After starting the timer, the trigger mode select box is disabled.

        Parameters:
            None

        Returns:
            None
        """
        
        self.graph_update_timer.start(1)  # Update every 1 millisecond
        self.triggerModeSelectBox.setEnabled(
            False
        )  # Disable the trigger mode select box

    def stop_graph_update_timer(self):
        """
        Stops the graph update timer and updates the UI elements accordingly.

        If the graph update timer is active, it is stopped. The text of the startAquisitionButton is set to "Start Acquisition",
        and the triggerModeSelectBox is enabled.

        Parameters:
            None

        Returns:
            None
        """
        if self.graph_update_timer.isActive():
            self.graph_update_timer.stop()
        self.startAquisitionButton.setText("Start Acquisition")
        self.triggerModeSelectBox.setEnabled(True)  # Enable the trigger mode select box

    def wait_for_ext_trig(self):
        """
        Waits for an external trigger signal and updates the graph when data is ready.

        This method connects the `update_graph` method to a timer that periodically checks if the spectrometer
        has received an external trigger signal. If the spectrometer has received the signal and data is ready,
        the `update_graph` method is called to update the graph.

        Note: The `isSpecConnected` attribute must be set to `True` before calling this method.

        Raises:
            Exception: If an error occurs while setting up the timer or connecting the signal.

        """
        if self.isSpecConnected:
            try:
                # def update_graph():
                #     if self.spectrometer.IsDataReady():
                #         self.update_graph()
                #         self.ext_trig_timer.start(10)  # Restart the timer
                # self.ext_trig_timer.timeout.connect(self.update_graph)
                # self.ext_trig_timer.start(10)  # Start the timer
                self.update_graph()
            except Exception as e:
                print(e)

    def update_graph(self):
        """
        Update the graph with the latest spectrum data.

        This method is responsible for updating the graph with the latest spectrum data
        received from the spectrometer. It performs various operations such as background
        subtraction, finding spectral peaks, updating maximum intensity readout, and
        adjusting the y-axis limits of the graph.

        Returns:
            None
        """
        st = time.time()
        if self.isSpecConnected:
            if not self.spectrometer.IsDataReady() or not self.spectrometer.GetTriggerLockout():
                # print("Data not ready")
                time.sleep(0.001)
                return
            
            # return if it's been less that 1/30 seconds (limit max readout to 30 hz):
            if time.time() - self.st_time < 0.005:
                return
            
            spectrum = np.array(self.spectrometer.ReadSpectrumBuffer())

            
            # if do_bkg_subtract:
            #     spectrum = spectrum - self.background

            max_intensity, max_index = self.max_value(spectrum)
            self.maxValueReadout.setText(f"{max_intensity:.2f}")
            self.MaxValueWavelengthReadout.setText(
                f"{self.wavelengths[max_index]:.2f} nm"
            )

            if self.plotSpectralPeakCheck.isChecked():
                print("Fix the peak plotting dumbass")
            #     self.find_spectral_peaks_LIBS(spectrum)
            # else:
            #     for i in self.libsLines:
            #         i.set_visible(False)
            #     self.LineIntensitiesLabel.setText("")


            self.spectraGraph.clear()
            self.spectraGraph.plot(self.wavelengths, spectrum, pen=self.pen)  

            if self.guessCarbonCheck.isChecked():
                carbon = self.guess_carbon(spectrum)
                self.carbonGuessLabel.setText(f"\nCarbon: {carbon}")

            else:
                self.carbonGuessLabel.setText("")


            if self.markMaxCheck.isChecked():
                max_intensity, max_index = self.max_value(spectrum)
                self.maxValueReadout.setText(f"{max_intensity:.2f}")
                self.MaxValueWavelengthReadout.setText(f"{self.wavelengths[max_index]:.2f} nm")
                self.maxIntensityLocation.setData([self.wavelengths[max_index]], [max_intensity])
                self.spectraGraph.addItem(self.maxIntensityLocation)
            else:
                self.maxIntensityLocation.clear()

            if self.autoscaleY_check.isChecked():
                self.spectraGraph.setYRange(0, np.max(spectrum)+ 500)
            else:
                if self.spectraGraph.viewRange()[1][1] != 65535:
                    self.spectraGraph.setYRange(0, 65535)

            if (self.saveFileCheck.isChecked() and self.triggerModeSelectBox.currentText() != "Continuous"):
                self.save_spectrum_async(spectrum)
            
            # while not self.spectrometer.GetTriggerLockout():
            #     print("waiting for trigger lock")
            #     pass
            self.spectrometer.ResetSpectrumBuffer()
            self.spectrometer.StartExposure()
            
            try:
                self.repratedisplay.setText(f"Refresh Rate: {int(1 / (time.time() - self.st_time))} Hz")
                print(f"Refresh Rate: {int(1 / (time.time() - self.st_time))} Hz")
            except:
                pass
            
            self.st_time = time.time()

    def save_spectrum_async(self, spectrum):
        """
        Asynchronously saves the spectrum and background data to a file.

        Args:
            spectrum: The spectrum data to be saved.
            bkg: The background data to be saved.

        Returns:
            None
        """
        threading.Thread(target=self.save_file, args=(spectrum,)).start()

    def update_trigger_delay(self):
        """
        Updates the trigger delay value for the spectrometer.

        This function retrieves the trigger delay value from the triggerDelayEntry widget,
        converts it to a float, and sets the trigger delay for the spectrometer using the
        SetTriggerDelay method. If the trigger delay is successfully set, the triggerDelayLabel
        widget's background color is set to green for 5 seconds. If an error occurs during the
        process, an error message is printed and the triggerDelayEntry widget is set to "Error".

        Parameters:
        None

        Returns:
        None
        """
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

    def handle_load_ml_model(self):
        file_dialog = QtWidgets.QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open ML Model", "", "ML Model (*.pkl)")
        if file_path:
            self.ml_model = joblib.load(file_path)
            self.mlModelLabel.setText("/".join(file_path.split("/")[-2:]))
            self.mlModelLabel.setStyleSheet("color: green")
            self.guessCarbonCheck.setEnabled(True)
        else:
            self.mlModelLabel.setText("No model selected")
            self.mlModelLabel.setStyleSheet("color: red")
            self.guessCarbonCheck.setEnabled(False)

    def guess_carbon(self, spectrum):
        try:
            carbon = self.ml_model.predict(spectrum.reshape(1, -1))
        except Exception as e:
            print(e)

            return "NaN"
        return carbon

    def handle_update_save_path(self):
        """
        Opens a file dialog to select a directory path and updates the filepath accordingly.
        If a directory path is selected, it updates the filePathLabel with the selected path
        and enables the saveFileCheck checkbox. Otherwise, it disables the saveFileCheck checkbox.
        """
        file_dialog = QtWidgets.QFileDialog()
        directory_path = file_dialog.getExistingDirectory(self, "Select Directory")
        if directory_path:
            self.filepath = directory_path
            self.filePathLabel.setText(directory_path)
            self.saveFileCheck.setEnabled(True)  # Enable the saveFileCheck checkbox
        else:
            self.saveFileCheck.setEnabled(False)  # Disable the saveFileCheck checkbox

    def save_file(self, spectra):
        """
        Save the spectra data to an HDF5 file.

        Args:
            spectra (numpy.ndarray): The intensity values of the spectra.
            bkg (int, optional): Flag indicating whether the spectra is background subtracted. Defaults to 0.

        Returns:
            None
        """
        if self.filepath:
            st = time.time()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]

            file_name = f"spectra_{self.shotnum:07}_{timestamp}.h5"

            file_path = os.path.join(self.filepath, file_name)

            with h5py.File(file_path, "w") as hdf_file:
                hdf_file.create_dataset("Wavelength", data=self.wavelengths)
                hdf_file.create_dataset("Intensity", data=spectra)
                hdf_file.attrs["User"] = self.user_entry.text()
                hdf_file.attrs["Timestamp"] = timestamp
                hdf_file.attrs["Integration Time"] = self.integrationTimeEntry.text()
                hdf_file.attrs["Trigger Delay"] = self.triggerDelayEntry.text()
                hdf_file.attrs["Trigger Mode"] = self.triggerModeSelectBox.currentText()
                hdf_file.attrs["PCB S/N"] = self.pcb_sn_label.text().split(":")[-1].strip()
                hdf_file.attrs["Spectrometer S/N"] = self.spec_sn_label.text().split(":")[-1].strip()
                hdf_file.attrs["Firmware"] = self.firmware_label.text().split(":")[-1].strip()
                hdf_file.attrs["Q Switch Delay"] = self.viron_qsdelay_entry.text()
                hdf_file.attrs["Wavelength"] = self.wavelength_entry.text()
                hdf_file.attrs["Sample ID"] = self.sample_id_entry.text()
                hdf_file.attrs["Focal Length"] = self.focal_length_entry.text()
                hdf_file.attrs["Fiber Angle"] = self.fiber_angle_entry.text()
                hdf_file.attrs["Shot Burst Number"] = self.bstnum if self.currentstate == 'burst' else 1
                hdf_file.attrs["Shot Number"] = f"{self.shotnum:07}"
                self.shotnum += 1
                try:
                    for i in self.status.keys():
                        hdf_file.attrs[i] = self.status[i]
                except:
                    print("No Viron status data availible - it aint connected boi")

            print(f"File saved: {file_path}\n Time taken: {time.time() - st:.2f} s\n\n")
        else:
            print("Error: Directory not chosen. File not saved.")


    def find_spectral_peaks_LIBS(self, spectrum):
        """
        Finds the spectral peaks in the given spectrum and updates the visibility of LIBS lines accordingly.
        
        Args:
            spectrum (numpy.ndarray): The spectrum data.
        
        Returns:
            None
        """
        st = ""
        peak_value, peak_index = self.max_value(spectrum)
        for index, name in enumerate(self.LIBS_line_names):
            intensity = spectrum[np.abs(self.wavelengths - self.LIBS_line_values[index]).argmin()] / peak_value
            if intensity > self.detectionThreshold:
                self.libsLines[index].set_visible(True)
                wavelength = self.LIBS_line_values[index]
                st += f"{name} ({wavelength:.1f}nm): {intensity:.3f}\n"
            else:
                self.libsLines[index].set_visible(False)
        
        # Split the string into six columns
        columns = 2
        lines = st.split("\n")
        num_lines = len(lines)
        col_width = num_lines // columns + 1
        
        # Create six columns
        cols = [[] for _ in range(columns)]
        for i, line in enumerate(lines):
            cols[i % columns].append(line)
        
        # Combine the columns with appropriate spacing
        combined = ""
        for i in range(max(num_lines // columns, num_lines % columns)):
            for col in cols:
                if i < len(col):
                    combined += f"{col[i]:<30}"
                else:
                    combined += " " * 30
            combined += "\n"
        
        self.LineIntensitiesLabel.setText(combined)

    
    # raster functions

    def calc_rect_raster(self, width, height, num_shots):
        """
        Calculate the raster pattern for a rectangular area.
        
        Input:
        - width (float): The width of the area to raster in mm.
        - height (float): The height of the area to raster in mm.
        - num_shots (int): The number of shots to take.
        
        Return:
        - raster (list): A list of tuples containing the x and y coordinates of each shot.
        """
        x = np.linspace(-width / 2, width / 2, int(np.sqrt(num_shots)))
        y = np.linspace(-height / 2, height / 2, int(np.sqrt(num_shots)))
        raster = []
        for i in x:
            for j in y:
                raster.append((i, j))
        return raster
    
    '''
    Does not work. 
    def calc_circ_raster(radius, num_shots):
        """
        Calculate the raster pattern for a circular area with concentric circles.
        
        Input:
        - radius (float): The radius of the circle to raster in mm.
        - num_shots (int): The number of shots to take.
        
        Return:
        - raster (list): A list of tuples containing the x and y coordinates of each shot.
        """
        raster = []
        raster.append((0, 0))  # Add shot at the origin
        radii = np.arange(0, radius+2, 2)

        circ_shot_nums = [(i+1)**2 - i**2 for i in range(int(np.sqrt(num_shots)))]
        print(circ_shot_nums)
        print(radii)
        i = 2
        while len(raster)  < num_shots:
            num = (i+1)**2 - i**2
            angles = [2 * np.pi / num * k for k in range(num)]
            for z, k in enumerate(angles):
                x = i * radii[i-2] * np.cos(k * z)
                y = i * radii[i-2] * np.sin(k * z)
                raster.append((x, y))
                if len(raster) == num_shots:
                    return raster
            i += 1
        
        return raster
        '''


    def update_qsdelay_calculator(self):
        self.qsdelaycalc_entry.blockSignals(True)
        self.energycalc_entry.blockSignals(True)
        qsdelay = self.qsdelaycalc_entry.text()
        try:
            qsdelay = int(qsdelay)
            if qsdelay in range(110, 180):
                
                self.energycalc_entry.setText(str(self.qsdelay_to_energy(qsdelay))[:5])
            else:
                self.energycalc_entry.setText("Invalid Q-Switch Delay")
        except: 
            pass
        self.qsdelaycalc_entry.blockSignals(False)
        self.energycalc_entry.blockSignals(False)
        
    def update_energy_calculator(self):
        self.qsdelaycalc_entry.blockSignals(True)
        self.energycalc_entry.blockSignals(True)
        energy = self.energycalc_entry.text()
        try:
            energy = float(energy)
            if energy >= 2. and energy <= 23.:
                self.qsdelaycalc_entry.setText(str(int(self.energy_to_qsdelay(energy))))
            else:
                self.qsdelaycalc_entry.setText("Invalid Energy")
        except: 
            pass
        self.qsdelaycalc_entry.blockSignals(False)
        self.energycalc_entry.blockSignals(False)


    def qsdelay_to_energy(self, qsdelay):
         return -2.49472087e-05*qsdelay**3 +  1.04262948e-02*qsdelay**2 + -1.10911264e+00*qsdelay + 3.10094968e+01
    
    def energy_to_qsdelay(self, energy):
         return 2.72139206e-03*energy**3 +  -9.21125442e-02*energy**2 + 3.91357395e+00*energy + 1.02617550e+02
        

    def max_value(self, arr):
        max_value = np.max(arr)
        max_index = np.argmax(arr)
        return max_value, max_index

    def on_close(self, event):
        print("Tidying up")
        if self.laser:
            self.laser.send_command("$STOP")
            res = self.laser.close()
            print(res)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
