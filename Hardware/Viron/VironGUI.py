import sys
from Viron import VironLaser
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QLabel, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,QFormLayout, QSlider
import time
from telnetGUI import TelnetSessionGUI

class LaserControlGUI(QMainWindow):
    # todo: add disconnect logic
    def __init__(self, host, port, password):
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.tn = None
        self.tngui = TelnetSessionGUI()
        self.currentstate = None
        self.connected = False
        self.states = ['standby', 'stop', 'fire', 'single_shot']
        self.laser_simple_status = {"isReady" : 'Disconnected'}
        self.laser = VironLaser(self.host, self.port, self.password, telnetgui=self.tngui)
        self.tngui.set_laser(self.laser)
        
        # Set up GUI
        self.create_gui()
        
        # Set up laser status timer:
        # Status timer only starts when connected to laser
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.handle_get_status)
        self.status_timer.setInterval(5000)
        
        
        
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

        self.status_label.setText(status_text_1)
        self.status_label_2.setText(status_text_2)

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
        temps = self.laser.get_temps()
        status_text += "Temperatures:\n"
        status_text += f"  Laser Temp: {temps['Laser Temp']} C\n"
        status_text += f"  Diode Temp: {temps['Diode Temp']} C\n"
        self.critical_status_label.setText(status_text)
        self.laser_status_label.setText(self.laser_simple_status['isReady'])

    def handle_set_qs_delay(self):
        '''
        Handles the action when the "Set Q-Switch Delay" button is clicked.
        '''
        delay = self.qs_delay_layout.get_value()
        if delay.isdigit():
            if self.laser.set_qs_delay(int(delay)):
                print('Q-Switch Delay Set to ', delay)
                return True
        return False
    
    def handle_set_qs_pre(self):
        '''
        Handles the action when the "Set Q-Switch pre" button is clicked.
        '''
        delay = self.qswitch_pre_layout.get_value()
        if delay.isdigit():
            if self.laser.set_qs_pre(int(delay)):
                print('Q-Switch Pre Set to ', delay)
                return True
        return False
    
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

    def _print_status(self, status):
        """
        Prints the status dictionary to the console.

        Args:
            status (dict): The status dictionary containing key-value pairs.

        Returns:
            None
        """
        print("Status:")
        print("-------")
        i = 0
        for key, value in status.items():
            if i % 8 == 0:
                print()
            print(f'   {key}: {value}')
            i += 1


    def handle_set_rep_rate(self):
        """
        Handles the action when the "Set Rep Rate" button is clicked.
        Retrieves the repetition rate value from the text entry and sets it on the laser.

        Returns:
            None
        """
        rate = self.rep_rate_layout.get_value()
        if rate.isdigit():
            self.laser.set_rep_rate(int(rate))

    def handle_get_status(self, status_hex=None):
        """
        Handles the action when the "Get Status" button is clicked.
        Retrieves the laser status hex value and parses it into a status dictionary.
        Then, it displays the status on the GUI.

        Returns:
            None
        """
        if status_hex is None:
            if self.connected:
                status_hex = self.laser.get_status()
            else:
                return
        if status_hex is not None:   
            status = self._parse_status(status_hex)
            
        self.display_status(status)
        self.display_critical_info(status)
        self._get_values()

    def handle_connect_to_laser(self):
        """
        Handles the action when the "Connect" button is clicked.
        Attempts to connect to the laser using the provided host, port, and password.
        Updates the GUI with the connection status.

        Returns:
            None
        """
        if self.laser.connect_to_laser():
            self.status_label.setText("Connected")
            self.connect_button.setStyleSheet("background-color: green")
            self.status_timer.start()
            self.connected = True

        else:
            self.status_label.setText("Connection Failed")
            self.connect_button.setStyleSheet("background-color: red")
            self.connected = False

    def handle_alignment_mode(self):
        self.laser.set_alignment_mode()
        self.start_var.setChecked(False)
        self.stop_var.setChecked(False)
        self.single_shot_var.setChecked(False)
        self.standby_var.setChecked(False)
        # self.set_alignment_button.setStyleSheet("background-color: lightgreen")
        self.single_shot_var.setStyleSheet("background-color : lightgrey")
        self.standby_var.setStyleSheet("background-color : lightgrey")
        self.stop_var.setStyleSheet("background-color : lightgrey")
        self.start_var.setStyleSheet("background-color : lightgrey")
        
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
            self.start_var.setChecked(False)
            self.stop_var.setChecked(False)
            self.single_shot_var.setChecked(False)
            self.single_shot_var.setStyleSheet("background-color : lightgrey")
            self.standby_var.setStyleSheet("background-color : lightgreen")
            self.stop_var.setStyleSheet("background-color : lightgrey")
            self.start_var.setStyleSheet("background-color : lightgrey")
            # self.set_alignment_button.setStyleSheet("background-color: lightgrey")
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
        if self.currentstate == 'stop' and self.stop_var.isChecked():
            return True
        
        if self.laser.set_stop():
            self.currentstate = 'stop'
            self.standby_var.setChecked(False)
            self.start_var.setChecked(False)
            self.single_shot_var.setChecked(False)
            self.single_shot_var.setStyleSheet("background-color : lightgrey")
            self.standby_var.setStyleSheet("background-color : lightgrey")
            self.stop_var.setStyleSheet("background-color : lightgreen")
            self.start_var.setStyleSheet("background-color : lightgrey")
            # self.set_alignment_button.setStyleSheet("background-color: lightgrey")
            return True
        else:
            print("failed to set stop")
            return False


    def toggle_auto_fire(self):
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
        
        self.standby_var.setChecked(False)
        self.stop_var.setChecked(False)
        self.single_shot_var.setChecked(False)
        self.single_shot_var.setStyleSheet("background-color : lightgrey")
        self.standby_var.setStyleSheet("background-color : lightgrey")
        self.stop_var.setStyleSheet("background-color : lightgrey")
        self.start_var.setStyleSheet("background-color : red")
        # self.set_alignment_button.setStyleSheet("background-color: lightgrey")

    def handle_set_single_shot(self):
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

            self.standby_var.setChecked(False)
            self.stop_var.setChecked(False)
            self.start_var.setChecked(False)
            self.standby_var.setStyleSheet("background-color : lightgrey")
            self.stop_var.setStyleSheet("background-color : lightgrey")
            self.start_var.setStyleSheet("background-color : lightgrey")
            self.single_shot_var.setStyleSheet("background-color : red")
            # self.set_alignment_button.setStyleSheet("background-color: lightgrey")
            
        if self.laser.fire_single_shot():
            print("fired mah lazor")
        
    def toggle_external_fire(self):
        self.currentstate = "external fire"
        if self.laser.set_external_trigger():
            self.external_shot_var.setStyleSheet("background-color : green")
            self.standby_var.setStyleSheet("background-color : lightgrey")
            self.stop_var.setStyleSheet("background-color : lightgrey")
            self.start_var.setStyleSheet("background-color : lightgrey")  
            self.single_shot_var.setStyleSheet("background-color : lightgrey")
            return True
        else:
            print("failed to set external trigger")
            return False   
   
    def handle_set_diode_current(self):
        if self.laser.send_command("$DCURR " + str(self.diode_current_layout.get_value())):
            print("Diode Current Set to ", self.diode_current_layout.get_value())
        else:
            print("Diode Current Not Set")
             
    def handle_set_diode_pulse_width(self):
        if self.laser.send_command("$DPW " + str(self.diode_pulse_width_layout.get_value())):
            print("Diode Pulse Width Set to ", self.diode_pulse_width_layout.get_value())
        else:
            print("Diode Pulse Width Not Set")
    
    def _get_values(self):
        qs_delay = self.laser.send_command('$QSDELAY ?', response=True)
        qs_pre = self.laser.send_command('$QSPRE ?', response=True)
        qsdivby = self.laser.send_command('$QSDIVBY ?', response=True)
        
       
        if qs_delay:
            self.qs_delay_layout.set_value(str(qs_delay.split()[1]))
        if qs_pre:
            self.qswitch_pre_layout.set_value(str(qs_pre).split()[1])
        if qsdivby:
            self.rep_rate_layout.set_value(str(20 / int(str(qsdivby).split()[1])))  
        
    def on_close(self):
        res = self.laser.close()
        print(res)
        
    def create_gui(self):
        """
        Creates and sets up the graphical user interface (GUI) for the Laser Control application.

        Returns:
            None
        """
        self.setWindowTitle("Laser Control")
        # self.setGeometry(100, 100, 300, 200)
        self.setWindowFlags(Qt.Window)  # Set window flags to allow resizing?

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        tab_widget = QTabWidget()

        # First tab
        first_tab = QWidget()
        first_tab_layout = QVBoxLayout(first_tab)
        first_tab_layout.setAlignment(Qt.AlignTop)  # Align contents to the top

        form_layout = QFormLayout()
        host_label = QLabel("Host:")
        host_entry = QLineEdit()
        host_entry.setText(self.host)  # Insert the default host value
        form_layout.addRow(host_label, host_entry)

        port_label = QLabel("Port:")
        port_entry = QLineEdit()
        port_entry.setText(str(self.port))  # Insert the default port value
        form_layout.addRow(port_label, port_entry)

        password_label = QLabel("Password:")
        password_entry = QLineEdit()
        password_entry.setText(self.password)  # Insert the default password value
        form_layout.addRow(password_label, password_entry)

        first_tab_layout.addLayout(form_layout)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.handle_connect_to_laser)
        first_tab_layout.addWidget(self.connect_button)

        buttons_layout = QHBoxLayout()
        self.standby_var = QPushButton("Standby")
        self.standby_var.setCheckable(True)
        self.standby_var.setChecked(False)  # Set the default value
        self.standby_var.clicked.connect(self.toggle_standby)
        self.standby_var.setStyleSheet("background-color : lightgrey")
        buttons_layout.addWidget(self.standby_var)

        self.stop_var = QPushButton("Stop")
        self.stop_var.setChecked(False)  # Set the default value
        self.stop_var.setCheckable(True)
        self.stop_var.clicked.connect(self.toggle_stop)
        self.stop_var.setStyleSheet("background-color : lightgrey")
        buttons_layout.addWidget(self.stop_var)

        self.start_var = QPushButton("Auto Fire")
        self.start_var.clicked.connect(self.toggle_auto_fire)
        self.start_var.setStyleSheet("background-color : lightgrey")
        self.start_var.setChecked(False)  # Set the default value
        self.start_var.setCheckable(True)
        buttons_layout.addWidget(self.start_var)

        self.single_shot_var = QPushButton("Single Fire")
        self.single_shot_var.clicked.connect(self.handle_set_single_shot)
        self.single_shot_var.setStyleSheet("background-color : lightgrey")
        self.single_shot_var.setChecked(False)  # Set the default value
        self.single_shot_var.setCheckable(True)
        buttons_layout.addWidget(self.single_shot_var)
        
        self.external_shot_var = QPushButton("External Fire")
        self.external_shot_var.clicked.connect(self.toggle_external_fire)
        self.external_shot_var.setStyleSheet("background-color : lightgrey")
        self.external_shot_var.setChecked(False)  # Set the default value
        self.external_shot_var.setCheckable(True)
        buttons_layout.addWidget(self.external_shot_var)

        first_tab_layout.addLayout(buttons_layout)


        self.rep_rate_layout = InputLayout("Repetition Rate (Hz)", func=self.handle_set_rep_rate)
        first_tab_layout.addLayout(self.rep_rate_layout)
        
        self.qs_delay_layout = InputLayout("Q-Switch Delay (us)", func=self.handle_set_qs_delay)
        # # self.set_alignment_button = QPushButton("Set Alignment (Not Implemented)")
        # # self.set_alignment_button.clicked.connect(self.handle_alignment_mode)
        # self.qs_delay_layout.addWidget(# self.set_alignment_button)
        first_tab_layout.addLayout(self.qs_delay_layout)

        self.qswitch_pre_layout = InputLayout("Q-Switch PrePulse (us)", func=self.handle_set_qs_pre)
        first_tab_layout.addLayout(self.qswitch_pre_layout)


        
        # critical status layout text box
        critical_status_layout = QHBoxLayout()
        self.laser_status_label = QLabel(self.laser_simple_status['isReady'])
        self.laser_status_label.setAlignment(Qt.AlignVCenter)
        self.laser_status_label.setAlignment(Qt.AlignHCenter)
        
        critical_status_label = QLabel("Status:")
        critical_status_label.setAlignment(Qt.AlignVCenter)
        critical_status_label.setAlignment(Qt.AlignRight)
        self.critical_status_label = QLabel()
        critical_status_layout.addWidget(self.laser_status_label)
        critical_status_layout.addWidget(critical_status_label)
        critical_status_layout.addWidget(self.critical_status_label)
        # get status button for first page
        get_status_button_firstpage = QPushButton("Get Status: (Updates every 5 seconds)")
        get_status_button_firstpage.clicked.connect(lambda: self.handle_get_status())
        critical_status_layout.addWidget(get_status_button_firstpage)
        
        first_tab_layout.addLayout(critical_status_layout)

        # Add the first tab to the tab widget
        tab_widget.addTab(first_tab, "Laser Control")

        # Second tab
        second_tab = QWidget()
        second_tab_layout = QVBoxLayout(second_tab)

        status_layout = QHBoxLayout()

        status_label = QLabel("Status:")
        self.status_label = QLabel()

        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_label)

        second_tab_layout.addLayout(status_layout)

        # Create a new QLabel for the second label
        self.status_label_2 = QLabel()
        status_layout.addWidget(self.status_label_2)

        get_status_button = QPushButton("Get Status")
        get_status_button.clicked.connect(lambda: self.handle_get_status())
        status_layout.addWidget(get_status_button)
        
        self.handle_get_status("0x000000000000")

        second_tab_layout.addLayout(status_layout)

        # Add the second tab to the tab widget
        tab_widget.addTab(second_tab, "Status")


        fourth_tab = QWidget()
        fourth_tab_layout = QVBoxLayout(fourth_tab) 
        fourth_tab_layout.addWidget(self.tngui)
        tab_widget.addTab(fourth_tab, "Telnet Session")
        main_layout.addWidget(tab_widget)
        self.show()
        
class InputLayout(QHBoxLayout):
    """
    A custom QHBoxLayout representing an input layout with a label, QLineEdit, and a QPushButton.

    Attributes:
        label (QLabel): QLabel widget displaying the text description of the input.
        entry (QLineEdit): QLineEdit widget for the user to enter input.
    """

    def __init__(self, text, defaultvalue=0, parent=None, func=None):
        """
        Initializes the InputLayout widget.

        Args:
            text (str): The text description of the input.
            defaultvalue (str or int, optional): The default value for the QLineEdit (default: 0).
            parent (QWidget, optional): The parent widget to which this widget will be added (default: None).
            func (callable, optional): The function to be called when the QPushButton is clicked (default: None).
        """
        super().__init__(parent)
        self.label = QLabel(text)
        self.entry = QLineEdit()
        self.entry.setText(str(defaultvalue))  # Set the default value (todo: parse first from laser)
        self.addWidget(self.label)
        self.addWidget(self.entry)

        set_button = QPushButton("Set " + text)
        if func:
            set_button.clicked.connect(func)
        self.addWidget(set_button)
        
    def get_value(self):
        """
        Returns the current text entered in the QLineEdit.

        Returns:
            str: The current text entered in the QLineEdit.
        """
        return self.entry.text()
    
    def set_value(self, text):
        """
        Sets the text of the QLineEdit.

        Args:
            text (str): The text to be set in the QLineEdit.
        """
        self.entry.setText(text)


        
              
if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        gui = LaserControlGUI(host='192.168.0.154', port=23, password='VR6BE4EE')
    except Exception as e:
        print(e)
        print("Something went wrong")
    finally:
        ret = app.exec_()
        gui.on_close()
        sys.exit(ret)     
