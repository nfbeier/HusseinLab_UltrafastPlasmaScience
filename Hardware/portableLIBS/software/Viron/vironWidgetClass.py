from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QWidget
)
from PyQt5.QtCore import QTimer, QTime
from PyQt5.uic import loadUi
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QDate

import time
# import h5py
from datetime import datetime
import sys, os

cwd = os.getcwd()
if 'portableLIBS' not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'portableLIBS' folder.")
# Rebuild the directory string up to and including 'portablelIBS', prevent import errors
cwd = os.path.sep.join(cwd.split(os.path.sep)[:cwd.split(os.path.sep).index('portableLIBS') + 1])
sys.path.insert(0,cwd)
os.chdir(cwd)

from software.Viron.vironWidget import Ui_Form
from software.Viron.Viron import VironLaser
from software.Viron.telnetGUI import TelnetSessionGUI

class VironWidget(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.is_viron_connected = False

        # connect button
        self.viron_connect_button.clicked.connect(self.handle_connect_to_laser)
        # standby button
        self.viron_standby_button.clicked.connect(self.toggle_standby)
        # stop button
        self.viron_stop_button.clicked.connect(self.toggle_stop)
        # auto fire button
        self.viron_autofire_button.clicked.connect(self.toggle_autofire)
        # single shot button
        self.viron_singlefire_button.clicked.connect(self.toggle_singlefire)
        # external fire button
        self.viron_external_fire_button.clicked.connect(self.toggle_external_fire)
        # set rep rate
        self.viron_set_reprate_button.clicked.connect(self.handle_set_rep_rate)
        # set qs delay
        self.viron_set_qsdelay_button.clicked.connect(self.handle_set_qs_delay)
        # set qs pre
        self.viron_qspre_set_button.clicked.connect(self.handle_set_qs_pre)
        # init statuses
        self.laser_simple_status = {"isReady" : 'Disconnected'}
        self.handle_get_status(status_hex="0x000000000000")
        # ----------------------------------------------------------------------------------------------
        self._init_viron()
        

        # ----------------------------------------------------------------------------------------------
    '''_______________________________________________________________________________________________________'''
    '''
        __     _____ ____   ___  _   _ 
        \ \   / /_ _|  _ \ / _ \| \ | |
         \ \ / / | || |_) | | | |  \| |
          \ V /  | ||  _ <| |_| | |\  |
           \_/  |___|_| \_\\___/|_| \_|
        _________________________________________________________________________________________________'''
        
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
            self.states = ['standby', 'stop', 'fire', 'single_shot']
            self.tngui_box.addWidget(self.tngui)
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.handle_get_status)
            self.status_timer.setInterval(5000)
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
                status_hex = self.laser.get_status()
            else:
                return
        if status_hex is not None:   
            status = self._parse_status(status_hex)
            
        self.display_status(status)
        self.display_critical_info(status)
        if self.is_viron_connected:
            self._get_values()
        
    def _get_values(self):
        qs_delay = self.laser.send_command('$QSDELAY ?', response=True)
        qs_pre = self.laser.send_command('$QSPRE ?', response=True)
        reprate = self.laser.send_command('$DFREQ ?', response=True)
        
       
        if qs_delay:
            self.viron_qsdelay_entry.setText(str(qs_delay.split()[1]))
        if qs_pre:
            self.viron_qspre_entry.setText(str(qs_pre).split()[1])
        if reprate:
            self.viron_reprate_entry.setText(str(reprate).split()[1])   
            
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
        status = {}

        # Byte 1
        status['Fire Mode'] = 'Disabled' if binary_string[0] == '0' else 'Fire'
        status['Standby Mode'] = 'Stop' if binary_string[1] == '0' else 'Standby'
        status['Diode Trigger Mode'] = 'Internal' if binary_string[2] == '0' else 'External'
        status['Q-Switch Mode'] = 'Internal' if binary_string[3] == '0' else 'External'
        status['Divide By Mode'] = 'Normal' if binary_string[4] == '0' else 'Divide By'
        status['Burst Mode'] = 'Continuous' if binary_string[5] == '0' else 'Burst'
        status['Q-Switch'] = 'Disabled' if binary_string[6] == '0' else 'Enabled'
        status['Ready'] = "Ready" if binary_string[7] == '0' else 'Not Ready'

        # Byte 2
        status['UV Illumination'] = 'Disabled' if binary_string[8] == '0' else 'Enabled'
        status['Remote Q-Switch'] = 'Normal Q-Switch' if binary_string[9] == '0' else 'Q-Switch off'
        status['50 Ohm Trigger Termination'] = 'Laser Disabled' if binary_string[10] == '0' else 'Enabled'
        status['BLE Session Temp'] = 'No Session' if binary_string[11] == '0' else 'Session'
        status['Diode TEC Running Temp'] = 'Off' if binary_string[12] == '0' else 'Run'
        status['LAN Session Temp'] = 'No Session' if binary_string[13] == '0' else 'Session'
        status['NLO Oven 2 Running Temp'] = 'Off' if binary_string[14] == '0' else 'Run'
        status['NLO Oven 1 Running Temp'] = 'Off' if binary_string[15] == '0' else 'Run'

        # Byte 3
        status['Remote Interlock Laser'] = 'No' if binary_string[16] == '0' else 'Yes'
        status['Laser Temperature Range'] = 'OK' if binary_string[17] == '0' else 'Fault'
        status['Charge Fault'] = 'OK' if binary_string[18] == '0' else 'Fault'
        status['Diode Current Fault'] = 'OK' if binary_string[19] == '0' else 'Fault'
        status['Diode Temperature High or Low'] = 'OK' if binary_string[20] == '0' else 'Fault'
        status['Diode Temperature Control Fault'] = 'OK' if binary_string[21] == '0' else 'Fault'
        status['System Interlock System/TEC Temp/Sys OK'] = 'OK' if binary_string[22] == '0' else 'Fault'
        status['System Interlock Laser Node'] = 'OK' if binary_string[23] == '0' else 'Fault'

        # Byte 4
        status['Reserved for BLE'] = 'No Action' if binary_string[24] == '0' else 'No Action'
        status['Reserved'] = 'No Action' if binary_string[25] == '0' else 'No Action'
        status['Operations Config Checksum'] = 'OK' if binary_string[26] == '0' else 'Fault'
        status['Factory Config Checksum'] = 'Ok' if binary_string[27] == '0' else 'Fault'
        status['CAN bus fault'] = 'OK' if binary_string[28] == '0' else 'Fault'
        status['Run time fault'] = 'OK' if binary_string[29] == '0' else 'Fault'
        status['RAM test fault'] = 'OK' if binary_string[30] == '0' else 'Fault'
        status['Watchdog Timeout'] = 'OK' if binary_string[31] == '0' else 'Fault'

        # Byte 5
        status['External Lamp PRF'] = 'OK' if binary_string[32] == '0' else 'PRF High'
        status['Laser Temperature Warning'] = 'OK' if binary_string[33] == '0' else 'Warning'
        status['Pre-Lase Detect/Q-Switch inhibited'] = 'OK' if binary_string[34] == '0' else 'Inhibited'
        status['CAN Bus Illegal ID or data'] = 'No' if binary_string[35] == '0' else 'Yes'
        status['CAN Bus Overrun'] = 'No' if binary_string[36] == '0' else 'Yes'
        status['Diode Current Limit'] = 'OK' if binary_string[37] == '0' else 'Warning'
        status['Reserved for Log Only - Temp Laser'] = 'Temp' if binary_string[38] == '0' else 'Laser'
        status['Diode/TEC Temp. Warning'] = 'OK' if binary_string[39] == '0' else 'Warning'

        # Byte 6
        status['NLO Oven 2 out of tolerance'] = 'No' if binary_string[40] == '0' else 'Yes'
        status['NLO Oven 2 timeout, oven 2 off'] = 'OK' if binary_string[41] == '0' else 'Warning'
        status['NLO Oven 2 over temp, oven 2 off'] = 'OK' if binary_string[42] == '0' else 'Warning'
        status['NLO Oven 2 open sensor, oven 2 off'] = 'OK' if binary_string[43] == '0' else 'Warning'
        status['NLO Oven 1 out of tolerance'] = 'No' if binary_string[44] == '0' else 'Yes'
        status['NLO Oven 1 timeout, oven 1 off'] = 'OK' if binary_string[45] == '0' else 'Warning'
        status['NLO Oven 1 over temp, oven 1 off'] = 'OK' if binary_string[46] == '0' else 'Warning'
        status['NLO Oven 1 open sensor, oven 1 off'] = 'OK' if binary_string[47] == '0' else 'Warning'


        # warming / rtf / fault
        if binary_string[16:47] == str('0'*31):
            self.laser_simple_status['isReady'] = 'Ready'
        elif binary_string[16:47] == str('0'*23 + '10000100') or str('0'*23 + '00000100'):
            self.laser_simple_status['isReady'] = 'Warming'
        else:
            self.laser_simple_status['isReady'] = 'Fault'        
        
        return status 
    

    def display_critical_info(self, status):
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
            temps = self.laser.get_temps()
            status_text += "Temperatures:\n"
            status_text += f"  Laser Temp: {temps['Laser Temp']} C\n"
            status_text += f"  Diode Temp: {temps['Diode Temp']} C\n"
        self.critical_status_label.setText(status_text)
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
            self.currentstate = 'standby'
            self.viron_autofire_button.setChecked(False)
            self.viron_stop_button.setChecked(False)
            self.viron_singlefire_button.setChecked(False)
            self.viron_singlefire_button.setStyleSheet("background-color : black")
            self.viron_standby_button.setStyleSheet("background-color : darkgreen")
            self.viron_stop_button.setStyleSheet("background-color : black")
            self.viron_autofire_button.setStyleSheet("background-color : black")
            self.viron_external_fire_button.setStyleSheet("background-color : black")
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
        if self.currentstate == 'stop' and self.viron_stop_button.isChecked():
            return True
        
        if self.laser.set_stop():
            self.currentstate = 'stop'
            self.viron_standby_button.setChecked(False)
            self.viron_autofire_button.setChecked(False)
            self.viron_singlefire_button.setChecked(False)
            self.viron_singlefire_button.setStyleSheet("background-color : black")
            self.viron_standby_button.setStyleSheet("background-color : black")
            self.viron_stop_button.setStyleSheet("background-color : darkgreen")
            self.viron_autofire_button.setStyleSheet("background-color : black")
            self.viron_external_fire_button.setStyleSheet("background-color : black")

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
        if self.currentstate != 'fire':
            # set to internal trigger
            self.laser.send_command("$QSON 1")
            self.laser.send_command("$TRIG II")
            
        if self.laser.set_fire():
            self.currentstate = 'fire'
        else:
            print("failed to set fire")
            return
        
        self.viron_standby_button.setChecked(False)
        self.viron_stop_button.setChecked(False)
        self.viron_singlefire_button.setChecked(False)
        self.viron_singlefire_button.setStyleSheet("background-color : black")
        self.viron_standby_button.setStyleSheet("background-color : black")
        self.viron_stop_button.setStyleSheet("background-color : black")
        self.viron_autofire_button.setStyleSheet("background-color : red")
        self.viron_external_fire_button.setStyleSheet("background-color : black")


    def toggle_singlefire(self):
        """
        Handles the action when the "Set Single Shot" button is clicked.
        Sets the laser in single shot mode and updates the GUI accordingly.

        Returns:
            None
        """
        if self.currentstate != 'single_shot':
            if self.laser.set_single_shot():
                self.currentstate = 'single_shot'
            else:
                print("Single Shot Not Set")
                return

            self.viron_standby_button.setChecked(False)
            self.viron_stop_button.setChecked(False)
            self.viron_autofire_button.setChecked(False)
            self.viron_standby_button.setStyleSheet("background-color : black")
            self.viron_stop_button.setStyleSheet("background-color : black")
            self.viron_autofire_button.setStyleSheet("background-color : black")
            self.viron_singlefire_button.setStyleSheet("background-color : red")
            self.viron_external_fire_button.setStyleSheet("background-color : black")

        if self.laser.fire_single_shot():
            print("fired mah lazor")  
            
    def toggle_external_fire(self):
        self.currentstate = 'external'
        if self.laser.set_external_trigger():
            self.viron_external_fire_button.setStyleSheet("background-color : darkgreen")
            self.viron_standby_button.setStyleSheet("background-color : black")
            self.viron_stop_button.setStyleSheet("background-color : black")
            self.viron_autofire_button.setStyleSheet("background-color : black")  
            self.viron_singlefire_button.setStyleSheet("background-color : black")
            return True
        else:
            print("failed to set external trigger")
            return False      
        
           
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
    
    def handle_set_qs_pre(self):
        '''
        Handles the action when the "Set Q-Switch pre" button is clicked.
        '''
        delay = self.viron_qspre_entry.text()
        if delay.isdigit():
            if self.laser.set_qs_pre(int(delay)):
                print('Q-Switch Pre Set to ', delay)
                return True
        return False
    
    
    
    
    # """
    #  _   _____________ _____ 
    # | | | |  _  \  ___|  ___|
    # | |_| | | | | |_  |___ \ 
    # |  _  | | | |  _|     \ \
    # | | | | |/ /| |   /\__/ /
    # \_| |_/___/ \_|   \____/ 
                            
    #  """

    # def set_directory(self):
    #     '''
    #     Opens a file browser in directory of LIBSGUI.py file.
    #     '''
    #     dir_path=QtWidgets.QFileDialog.getExistingDirectory(self,"Choose Directory","./")  # Change the 3rd parameter ("./") to change directory that browser opens in.
    #     self.SaveData_dir = dir_path
    #     self.save_data_dir_label.setText(dir_path)

    # def get_MetaData(self):
    #     md = {}
    #     md["Time"] = datetime.now().strftime('%Y-%m-%dT%H%M%S%f')[:-3]
    #     md['LaserEnergy'] = self.laser_energy_entry.text()
    #     md['LaserWavelength'] = self.wavelength_entry.text()
    #     md['LaserPulseDuration'] = self.pulse_duration_entry.text()
    #     md["sampleID"] = self.sample_id_entry.text()
    #     md["FocalLength"] = self.focal_length_entry.text()
    #     md["IntegrationTime"] = self.integration_time_entry.text()
    #     md['FiberAngle'] = self.fiber_angle_entry.text()
    #     md["BackgroundSpectrum"] = self.background_spectra_present_select.currentText()
    #     md["AdditionalInfo"] = self.additional_info_entry.text()
    #     return md

    # def save_data_h5(self):
    #     #Save Data
    #     md = self.get_MetaData()
    #     hdf = h5py.File(self.SaveData_dir + '/' + "LIBS_Spectrum_{:05d}".format(self.file_num) + "_" + md["Time"] +'.h5', 'w')
        
    #     if self.are_specs_connected:
    #         wavs, spectras = self.spectraplotter.getSpectra()
            
    #         for i, x in enumerate(spectras):
    #             hdf.create_dataset('Spectrum_'+str(min(wavs[i]))[:3]+"_"+str(max(wavs[i]))[:3], data=[wavs[i], x])

    #     if self.is_scope_connected:
    #         # Ocilloscope_data = hdf.create_dataset('Ocilloscope_data', data=data_oci)
    #         pass
        
    #     if self.is_xps_connected:
    #         abs_pos = [self.x_xps.getStagePosition(self.x_axis), self.y_xps.getStagePosition(self.y_axis)]
        
    #     # deal with metadata:
    #     for i in md:
    #         hdf.attrs[i] = md[i]
    #     hdf.close()
            
    #     self.file_num += 1
    #     self.shot_number_label.setText(str(self.file_num))
    # """_______________________________________________________________________________________________________"""
     
    # def set_save(self, state):
    #     self.save = state
    #     self.savedata_label.setText(str(state))
     
    # def fire_laser_single(self):
    #     if self.are_specs_connected:
    #         self.arm_spectrometers()
    #         time.sleep(0.1)
            
    #     if self.is_scope_connected:
    #         scopethread = threading.Thread(target=self.scope.wait_for_trigger_and_get_data)
    #         scopethread.start()
            
    #     if self.is_dg645_connected:
    #         self.fire()
            

    #         # process data in separate thread
        
    #     if self.is_scope_connected:
    #         scopedata = scopethread.join()
    #         # asynchronusly update the scope plot
    #         threading.Thread(target=self._update_scope_plot, args=(scopedata,)).start()
        

    #     # need to save data here too
    #     if self.save:
    #         self.save_data_h5()
        
    #     if self.are_specs_connected:
    #         # join spectrometers
    #         self.update_plot()
            
            
    # def fire(self):
    #     self.dg645.sendcmd('*TRG') 
         

    # def _update_clock(self):
    #     current_date_time = QDate.currentDate().toString() + ' ' + QTime.currentTime().toString()
    #     self.clock_label.setText(current_date_time)
     
    # def _is_float(self, string):
    #     if string.replace(".", "").isnumeric():
    #         return True
    #     else:
    #         return False
        
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout
    app = QApplication(sys.argv)

    main_window = QWidget()
    main_window.setWindowTitle("Ibsen Spectrometer UI")
    main_window.resize(1200, 700)  # Set the default window size

    layout = QVBoxLayout(main_window)
    grid_layout = QGridLayout()
    iris_gui = VironWidget()
    grid_layout.addWidget(iris_gui, 0, 0)

    layout.addLayout(grid_layout)

    main_window.setLayout(layout)

    main_window.show()

    sys.exit(app.exec_())