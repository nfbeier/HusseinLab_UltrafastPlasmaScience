#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 16:41:38 2026

@author: christina

i dedicate this gui to lisa vanderpump xx 
like her this gui is a bit of a mess but it works

Requirements:
    - Python 3.10 environment
    - PySpin (Spinnaker Python SDK)
    - numpy < 2  (PySpin was compiled against NumPy 1.x and is incompatible
      with NumPy 2.x. Install with: pip install "numpy<2")
    - pyqtgraph
"""

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import numpy as np
import time, sys
from time import sleep
import instruments as ik
import json
import csv
import os

# Script directory for saved position files
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add FLIR Camera Code directory to path for BlackflyCamera import
flir_code_dir = os.path.join(
    script_dir, os.pardir, "SolidTargetStage", "Camera Testing", "FLIR Camera Code"
)
if flir_code_dir not in sys.path:
    sys.path.insert(0, flir_code_dir)
from blackfly_camera import BlackflyCamera
import cv2


# Makes sure you are in the right path!
cwd = os.getcwd()
if "HusseinLab_UltrafastPlasmaScience" not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")
# Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience', prevent import errors
cwd = os.path.sep.join(
    cwd.split(os.path.sep)[: cwd.split(os.path.sep).index("HusseinLab_UltrafastPlasmaScience") + 1]
)
os.chdir(cwd)
sys.path.insert(0, cwd)

# Importing the control window
from Software.LaserAblationShadowgraph.main_control_pannel_gui import Ui_MainWindow

#Importing the Delay generator class 
from Hardware.DG645.dg645 import DelayGen

#Importing the XPS Class
from Hardware.XPS.XPS import XPS

class solid_target_stage_app_stage_app(QtWidgets.QMainWindow):
    def __init__(self):
        super(solid_target_stage_app_stage_app,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        ### ROTATION STAGE SETUP #######
        self.shot_sep = float(self.ui.shot_sep_ip.text())

        #Setting the start and stop values to -1 until the buttons are clicked
        self.x_start = -1
        self.x_stop = -1
        self.y_start = -1
        self.y_stop = -1
        
        # Tracks where the next scan should resume (None = start from x_start, y_start)
        self.scan_resume_pos = None
        
        
        ### DELAY GENERATOR SETUP #######
        
        #Connecting the delay generator instrument
        self.ins_dg = DelayGen("COM5", 9600) # dg645
        sleep(1)  # Give the DG645 time to initialize before sending commands
        
        
        ##### XPS STAGE SETUP ######
        self.xps = None
        self.xpsAxes = [None, None]
        
        # XPS GUI Setup
        self.ui.x_min_trav_ip.setText('0')
        self.ui.x_max_trav_ip.setText('46')
        
        self.ui.y_min_trav_ip.setText('0')
        self.ui.y_max_trav_ip.setText('25')
        
        self.ui.x_abs_mv_ip.setText('0')
        self.ui.y_abs_mv_ip.setText('0')
        
        self.ui.x_step_ip.setText('0')
        self.ui.y_step_ip.setText('0')
        
  
        ######### ROTATION GUI CONTROLS #########
       
        #Adjusting and updating the shot seperation value
        self.ui.shot_sep_ip.textChanged.connect(self.updateEffSep)
        
        
        #Buttons for clicing the start and stop buttons
        self.ui.set_x_start_bt.clicked.connect(self.SetStartXPos)
        self.ui.set_y_start_bt.clicked.connect(self.SetStartYPos)
        self.ui.set_x_stop_bt.clicked.connect(self.SetStopXPos)
        self.ui.set_y_stop_bt.clicked.connect(self.SetStopYPos)
        
        #Button for calculating the availble shots
        self.ui.avail_shot_bt.clicked.connect(self.CalcShotsAvail)
        
        # Button for setting T_zero
        self.ui.set_to_time.clicked.connect(self.SetT_Zero)
        
        # Button for resetting back to T_zero
        self.ui.set_time_2_to.clicked.connect(self.SetTime2T0)
        
        #Button for setting the scan paramters
        self.ui.set_scan_param.clicked.connect(self.SetScanParam)
        
        
        
        
        
        
        ######## DELAY GENERATOR FUNCTIONS ##########
        # Reads in previous input for different channel levels 
        self.read_json()
        
        # Set the saved trigger source on the device
        self.ins_dg.get_trg_src(self.saved_trig_src)
        self.ins_dg.set_trg_src()
        
        # Query and display the current trigger source to confirm
        current_trig_src = self.ins_dg.query_trg_src()
        self.ui.trig_src_disp.setText(current_trig_src)
        
        # Creating the user inputs / buttons for the gui 
        self.ui.delay_select.currentIndexChanged.connect(lambda: self.disp_ch("delay"))
        self.ui.voltage_select.currentIndexChanged.connect(lambda: self.disp_ch("voltage"))
         
        #Adjusting and updating the delay values 
        self.ui.channel_link.textChanged.connect(lambda: self.updateDelayvals("Channel_Link"))
        self.ui.delay_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Val"))
        self.ui.delay_select_units.currentIndexChanged.connect(lambda: self.updateDelayvals("Delay_Units"))
        
        #Adjusting and updating the voltage values
        self.ui.offset_v.textChanged.connect(lambda: self.updateVoltvals("Offset_Val"))
        self.ui.amplitude_v.textChanged.connect(lambda: self.updateVoltvals("Amp_Val"))
        
        #Selecting the trigger source 
        self.ui.trigger_source_select.currentIndexChanged.connect(self.trg_src_change)
        #Changing the trigger source 
        self.ui.set_trig_src_bt.clicked.connect(self.SetTrigSrc)
        
        # Loading and setting the previosuly saved file
        self.ui.set_json_bt.clicked.connect(self.SetSavedBt)
        
        # Setting the delay values 
        self.ui.set_delay_bt.clicked.connect(self.SetDelayBt)
        
        # Setting the voltage values 
        self.ui.set_level_bt.clicked.connect(self.SetVoltageBt)
        
        # Setting the relative delay
        self.ui.set_rel_delay_bt.clicked.connect(self.SetRelativeDelayBt)
        
        # #Buttons for displaying on the delay generator
        self.ui.T0_bt.clicked.connect(lambda: self.change_display_bt("T0"))
        self.ui.T1_bt.clicked.connect(lambda: self.change_display_bt("T1"))
        self.ui.A_bt.clicked.connect(lambda: self.change_display_bt("A"))
        self.ui.B_bt.clicked.connect(lambda: self.change_display_bt("B"))
        self.ui.C_bt.clicked.connect(lambda: self.change_display_bt("C"))
        self.ui.D_bt.clicked.connect(lambda: self.change_display_bt("D"))
        self.ui.E_bt.clicked.connect(lambda: self.change_display_bt("E"))
        self.ui.F_bt.clicked.connect(lambda: self.change_display_bt("F"))
        self.ui.G_bt.clicked.connect(lambda: self.change_display_bt("G"))
        self.ui.H_bt.clicked.connect(lambda: self.change_display_bt("H"))
        
        # Unit conversion factors to seconds
        self.unit_to_seconds = {
            "s"  : 1.0,
            "ms" : 1e-3,
            "us" : 1e-6,
            "ns" : 1e-9,
            "ps" : 1e-12,
        }
        
        
        
        ######## XPS FUNCTIONS ##########
        
        #Connect Command
        self.ui.connect_xps_bt.clicked.connect(self._initXPS)
        
        #Initialize, home, enable disable commands
        self.ui.init_xps_bt.clicked.connect(lambda: self.xpsStatusBtn("Initialize"))
        self.ui.home_xps_bt.clicked.connect(lambda: self.xpsStatusBtn("Home"))
        self.ui.enable_dis_xps_bt.clicked.connect(lambda: self.xpsStatusBtn("EnableDisable"))
        
        #Adjusting the minimum and maximum travel limits for the two stages
        self.ui.x_min_trav_ip.textChanged.connect(lambda: self.updateTravelLimits("minXPSX"))
        self.ui.x_max_trav_ip.textChanged.connect(lambda: self.updateTravelLimits("maxXPSX"))
        
        self.ui.y_min_trav_ip.textChanged.connect(lambda: self.updateTravelLimits("minXPSY"))
        self.ui.y_min_trav_ip.textChanged.connect(lambda: self.updateTravelLimits("maxXPSY"))
        
        #Moving the two stages
        self.ui.x_abs_mv_bt.clicked.connect(lambda: self.xpsMotionBtn("AbsoluteX"))
        self.ui.x_step_f_bt.clicked.connect(lambda: self.xpsMotionBtn("ForwardX"))
        self.ui.x_step_b_bt.clicked.connect(lambda: self.xpsMotionBtn("BackwardX"))
        
        self.ui.y_abs_mv_bt.clicked.connect(lambda: self.xpsMotionBtn("AbsoluteY"))
        self.ui.y_step_f_bt.clicked.connect(lambda: self.xpsMotionBtn("ForwardY"))
        self.ui.y_step_b_bt.clicked.connect(lambda: self.xpsMotionBtn("BackwardY"))
        
      
        
        ####### CAMERA SETUP ########
        self.cam = BlackflyCamera()
        self.cam_connected = False
        self.video_running = False
        self.last_saved_image = None
        self.image_counter = 0
        
        # Default save directory
        self.save_directory = os.path.join(script_dir, "FLIR Camera Images")
        
        # Hide ROI and menu buttons on the ImageView widget
        self.ui.CapturedImage.ui.roiBtn.hide()
        self.ui.CapturedImage.ui.menuBtn.hide()
        
        # Set up the video feed timer
        self.video_timer = QtCore.QTimer(self)
        self.video_timer.timeout.connect(self.update_video_feed)
        
        # Connect camera buttons
        self.ui.FindButton.clicked.connect(self.find_cameras_btn)
        self.ui.ConnectButton.clicked.connect(self.connect_camera)
        self.ui.StartVideoButton.clicked.connect(self.start_video)
        self.ui.StopVideoButton.clicked.connect(self.stop_video)
        self.ui.DisconnectButton.clicked.connect(self.disconnect_camera)
        self.ui.ModeComboBox.currentIndexChanged.connect(self.change_camera_mode)
        
        # Camera settings inputs
        self.ui.exposure_time_ip.editingFinished.connect(self.apply_exposure_time)
        self.ui.gain_ip.editingFinished.connect(self.apply_gain)
        self.ui.save_captured_img.clicked.connect(self.save_captured_image_btn)
        
        # Select save directory
        self.ui.select_save_dir.clicked.connect(self.selectSaveDirectory)
        
        # Setting the Start Button
        self.ui.start_scan_bt.clicked.connect(self.StartScan)
        
        # Test fire buttons (fire DG + capture image, no save/count)
        self.ui.fire_dg_bt_1.clicked.connect(self.TestFireDG)
        self.ui.fire_dg_bt_2.clicked.connect(self.TestFireDG)
        
        #Setting the  disconnect
        self.ui.stop_bt.clicked.connect(self.DisconnectBtn)
        
        # Initialize error message label
        self.ui.error_msg_label.setText('')
        # self.ui.error_msg_label.setStyleSheet("color: red;") # Removed initial color setting
        
        
        
        
    ######### Error Display Funcs#########  
    
    def display_error_message(self, message, error_type="ERROR"):
        """
        Display error/warning messages both in GUI and terminal.
        
        Args:
            message (str): The error message to display
            error_type (str): Type of message - "ERROR", "WARNING", or "INFO"
        """
        # Format message with timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {error_type}: {message}"
        
        # Print to terminal
        print(formatted_msg)
        
        # Display in GUI error label
        self.ui.error_msg_label.setText(message)
        
        # Set color based on error type
        if error_type == "ERROR":
            self.ui.error_msg_label.setStyleSheet("background-color: #ff9999; color: black; padding: 5px; border-radius: 4px;")
        elif error_type == "WARNING":
            self.ui.error_msg_label.setStyleSheet("background-color: #ffbd95; color: black; padding: 5px; border-radius: 4px;")
        elif error_type == "INFO":
            self.ui.error_msg_label.setStyleSheet("background-color: #b8dfa7; color: black; padding: 5px; border-radius: 4px;")
    
    def clear_error_message(self):
        """Clear the error message from GUI."""
        self.ui.error_msg_label.setText('')
        self.ui.error_msg_label.setStyleSheet('')
    

    ######### TARGET STAGE FUNCS#########  
    
    
    def updateEffSep(self):   
        self.shot_sep_prelim = self.ui.shot_sep_ip.text()
        if  self.shot_sep_prelim != '':
            self.shot_sep = float(self.shot_sep_prelim)
    
            
    
    def SetStartXPos(self):
        # Sets the value
        self.x_start = float(self.ui.x_pos_disp.toPlainText())

    def SetStartYPos(self):
        # Sets the value
        self.y_start = float(self.ui.y_pos_disp.toPlainText())
        
    def SetStopXPos(self):
        # Sets the value
        self.x_stop = float(self.ui.x_pos_disp.toPlainText())
        
    def SetStopYPos(self):
        # Sets the value
        self.y_stop = float(self.ui.y_pos_disp.toPlainText())
        
    def CalcShotsAvail(self):
        # Check that all start/stop positions have been set
        unset = []
        if self.x_start == -1:
            unset.append("X Start")
        if self.x_stop == -1:
            unset.append("X Stop")
        if self.y_start == -1:
            unset.append("Y Start")
        if self.y_stop == -1:
            unset.append("Y Stop")
        
        if unset:
            missing = ", ".join(unset)
            self.ui.raster_calc_disp.setText(f"Error: Set positions first - {missing}")
            return
        
        # Calculating the available target area (positions in mm)
        self.x_dim = abs(self.x_stop - self.x_start)
        self.y_dim = abs(self.y_stop - self.y_start)
        self.target_area = self.x_dim * self.y_dim
        
        # Calculating the effective shot area (shot_sep already in mm)
        self.shot_area = self.shot_sep ** 2 
        
        if self.shot_area == 0:
            self.ui.raster_calc_disp.setText("Error: Shot separation is zero")
            return
        
        # Getting the # of shots 
        avail_shot = int(self.target_area / self.shot_area)
        
        # Displaying the value 
        self.ui.raster_calc_disp.setText(f"There are {avail_shot} shots available")
        
     
    def SetT_Zero(self):
        t_zero_channel = self.ui.delay_select_to_sig.currentText()
        t_zero_step_dir = self.ui.exp_select_step_dir.currentText()
        if t_zero_step_dir == "Increase":
            self.t_zero_step_dir = 1
        elif t_zero_step_dir == "Decrease":
            self.t_zero_step_dir = -1
        
        # Store the channel used for T0
        self.t_zero_channel = t_zero_channel
        
        # Get the current delay value and units from the stored dg_values
        self.t_zero_delay = self.dg_values[t_zero_channel][1]
        self.t_zero_units = self.dg_values[t_zero_channel][2]
        
        # Convert to seconds for a universal reference
        self.t_zero_seconds = float(self.t_zero_delay) * self.unit_to_seconds[self.t_zero_units]
        
        print(f"T0 set: channel {self.t_zero_channel}, "
              f"delay {self.t_zero_delay} {self.t_zero_units} "
              f"({self.t_zero_seconds} s), direction: {self.t_zero_step_dir}")
              
    def SetTime2T0(self):
        if not hasattr(self, 't_zero_channel'):
            self.ui.raster_overview_disp_2.setText("Error: T0 not set. Cannot reset.")
            return
            
        channel = self.t_zero_channel
        channel_ref = self.dg_values[channel][0]
        delay = self.t_zero_delay
        delay_units = self.t_zero_units
        
        # Restore into memory
        self.dg_values[channel][1] = delay
        self.dg_values[channel][2] = delay_units
        
        # Update hardware
        self.ins_dg.get_delay(channel, channel_ref, delay, delay_units)
        sleep(0.1)
        self.ins_dg.set_delay()
        sleep(0.1)
        
        # Refresh the UI if that channel happens to be currently selected
        if self.ui.delay_select.currentText() == channel:
            self.disp_ch("delay")
            
        self.ui.raster_overview_disp_2.setText(f"Reset {channel} back to T0 ({delay} {delay_units})")
        print(f"Reset channel {channel} back to T0 time: {delay} {delay_units}")
    
    def SetScanParam(self):
        # First check if T0 has been properly assigned
        if not hasattr(self, 't_zero_seconds'):
            self.ui.raster_overview_disp_2.setText("Error: Set T0 first before configuring scan.")
            return
        
        # Then check if scan area has been defined (x_start, x_stop, y_start, y_stop)
        unset = []
        if self.x_start == -1:
            unset.append("X Start")
        if self.x_stop == -1:
            unset.append("X Stop")
        if self.y_start == -1:
            unset.append("Y Start")
        if self.y_stop == -1:
            unset.append("Y Stop")
        if unset:
            missing = ", ".join(unset)
            self.ui.raster_overview_disp_2.setText(f"Error: Set scan area first - {missing}")
            return
        
        # Check if a file directory was selected to save data
        if not hasattr(self, 'save_directory') or self.save_directory is None:
            self.ui.raster_overview_disp_2.setText("Error: Select a save directory first.")
            return
        
        # Load the values for the scan (these are all QLineEdits, use .text())
        try:
            self.shot_per_time_step = int(self.ui.scan_shot_select.text())
            self.time_step_seconds = float(self.ui.scan_time_step_disp.text()) * self.unit_to_seconds[self.ui.scan_step_time_unit_select.currentText()]
            self.rel_start_time_seconds = float(self.ui.scan_start_time_disp.text()) * self.unit_to_seconds[self.ui.scan_start_time_unit_select.currentText()]
            self.rel_stop_time_seconds = float(self.ui.scan_stop_time_disp.text()) * self.unit_to_seconds[self.ui.scan_stop_time_unit_select.currentText()]
        except ValueError:
            self.ui.raster_overview_disp_2.setText("Error: Invalid scan parameter values. Check inputs.")
            return
        
        # Validate time step is positive
        if self.time_step_seconds <= 0:
            self.ui.raster_overview_disp_2.setText("Error: Time step must be greater than zero.")
            return
        
        # Calculate how many time steps and total shots
        # Example: start=0, stop=10ns, step=2ns -> steps at 0, 2, 4, 6, 8, 10 ns = 6 steps
        # With 3 shots per step -> 6 * 3 = 18 total shots
        num_time_steps = int(round(abs(self.rel_stop_time_seconds - self.rel_start_time_seconds) / self.time_step_seconds)) + 1
        self.total_scan_shots = num_time_steps * self.shot_per_time_step
        
        # Build the array of time steps (in seconds, relative to T0)
        self.scan_time_steps = [
            self.rel_start_time_seconds + i * self.time_step_seconds 
            for i in range(num_time_steps)
        ]
        
        # Display the scan overview
        start_disp = self.ui.scan_start_time_disp.text()
        start_unit = self.ui.scan_start_time_unit_select.currentText()
        stop_disp = self.ui.scan_stop_time_disp.text()
        stop_unit = self.ui.scan_stop_time_unit_select.currentText()
        step_disp = self.ui.scan_time_step_disp.text()
        step_unit = self.ui.scan_step_time_unit_select.currentText()
        
        overview = (f"Scan: {start_disp} {start_unit} to {stop_disp} {stop_unit} "
                    f"in {step_disp} {step_unit} steps | "
                    f"{num_time_steps} time steps x {self.shot_per_time_step} shots = "
                    f"{self.total_scan_shots} total shots")
        
        self.ui.raster_overview_disp_2.setText(overview)
        
   
        
     
     ######### DELAY GEN FUNCTIONS ######### 
     
    #Reads in the json file
    def read_json(self):
        with open(os.path.join(script_dir, "delay_gen_gui_inputs.json"), "r") as read_file:
            inputs = json.load(read_file)
        self.dg_values = {
            "A" : [inputs["A_ch"], inputs["A_delay"], inputs["A_delay_unit"]],
            "B" : [inputs["B_ch"], inputs["B_delay"], inputs["B_delay_unit"]],
            "C" : [inputs["C_ch"], inputs["C_delay"], inputs["C_delay_unit"]],
            "D" : [inputs["D_ch"], inputs["D_delay"], inputs["D_delay_unit"]],
            "E" : [inputs["E_ch"], inputs["E_delay"], inputs["E_delay_unit"]],
            "F" : [inputs["F_ch"], inputs["F_delay"], inputs["F_delay_unit"]],
            "G" : [inputs["G_ch"], inputs["G_delay"], inputs["G_delay_unit"]],
            "H" : [inputs["H_ch"], inputs["H_delay"], inputs["H_delay_unit"]],
            "AB" : [inputs["AB_offset"], inputs["AB_Amp"]], 
            "CD" : [inputs["CD_offset"], inputs["CD_Amp"]], 
            "EF" : [inputs["EF_offset"], inputs["EF_Amp"]],
            "GH" : [inputs["GH_offset"], inputs["GH_Amp"]]
            }
        # Read trigger source if it exists in the JSON file
        self.saved_trig_src = inputs.get("trigger_source", "Internal")
        
    def disp_ch(self, widget):    
        if widget == "delay":
            channel = self.ui.delay_select.currentText()
            self.ui.channel_link.setText(self.dg_values[channel][0])
            
            # Clean floating point artifacts when displaying (preserve up to 14 decimals for ps precision in seconds)
            delay_val_rounded = round(float(self.dg_values[channel][1]), 14)
            self.ui.delay_disp.setText(str(delay_val_rounded))   
            self.ui.delay_select_units.setCurrentText(self.dg_values[channel][2])
            
            channel_ref = self.dg_values[channel][0]
            delay = self.dg_values[channel][1]
            delay_units = self.dg_values[channel][2]
            self.ins_dg.get_delay(channel, channel_ref, delay, delay_units)
            
        elif widget == "voltage":
            channel = self.ui.voltage_select.currentText()
            self.ui.offset_v.setText(str(self.dg_values[channel][0]))
            self.ui.amplitude_v.setText(str(self.dg_values[channel][1]))
            
            offset_v = self.dg_values[channel][0]
            amplitude_v = self.dg_values[channel][1]
            self.ins_dg.get_voltage(channel, offset_v, amplitude_v)
    
     
    def updateDelayvals(self, widget):
        channel = self.ui.delay_select.currentText()
        if widget == "Channel_Link" and (self.ui.channel_link.text() != ''):
            self.dg_values[channel][0] = str(self.ui.channel_link.text())
        elif widget == "Delay_Val" and (self.ui.delay_disp.text() != ''):
            delay = float(self.ui.delay_disp.text())
            self.dg_values[channel][1] = delay
        elif widget == "Delay_Units" and (self.ui.delay_select_units.currentText() != ''):
            delay_units = str(self.ui.delay_select_units.currentText())
            self.dg_values[channel][2] = delay_units
         
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.delay_select_units.currentText() != "":
            channel_ref = self.ui.channel_link.text()
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.delay_select_units.currentText())
            self.ins_dg.get_delay(channel, channel_ref, delay, delay_units)
            
            
    def updateVoltvals(self, widget):
        channel = self.ui.voltage_select.currentText()
        if widget == "Offset_Val" and (self.ui.offset_v.text() != ''):
            offset_val = float(self.ui.offset_v.text())
            self.dg_values[channel][0] = offset_val
        elif widget == "Amp_Val" and (self.ui.amplitude_v.text() != ''):
            amp_val = float(self.ui.amplitude_v.text())
            self.dg_values[channel][1] = amp_val
        
        if self.ui.offset_v.text() != "" and self.ui.amplitude_v.text() != "":
            offset_v = float(self.ui.offset_v.text())
            amplitude_v = float(self.ui.amplitude_v.text())
            self.ins_dg.get_voltage(channel, offset_v, amplitude_v)
    
    def trg_src_change(self):
        trg_src = self.ui.trigger_source_select.currentText()
        self.ins_dg.get_trg_src(trg_src)
    
    def SetTrigSrc(self):
        # Sets the value in case there was a change
        trg_src = self.ui.trigger_source_select.currentText()
        self.ins_dg.get_trg_src(trg_src)
        
        #Now setting the trigger source  
        self.ins_dg.set_trg_src()
        
        #Displaying this value
        current_trig_src = self.ins_dg.query_trg_src()
        self.ui.trig_src_disp.setText(current_trig_src)
   
    def change_display_bt(self, btn):       
        self.ins_dg.change_display(btn)
   
    def SetSavedBt(self):
        # Sets the saved json values
        i = 0
        for a in self.dg_values:
            if i < 0:
            
                channel = a
                channel_ref = self.dg_values[a][0]
                print(channel,channel_ref)
                delay = self.dg_values[a][1]
                delay_units = self.dg_values[a][2]
                #Get the delay
                self.ins_dg.get_delay(channel, channel_ref, delay, delay_units)
                #Confirm the link
                self.ins_dg.change_delay_link(channel, channel_ref)
                sleep(0.2)
                #Set the delay
                self.ins_dg.set_delay()
                
            elif i > 8:
                voltage_select = a
                offset_v = float(self.dg_values[a][0])
                amplitude_v = float(self.dg_values[a][1])
                self.ins_dg.get_voltage(voltage_select, offset_v, amplitude_v)
                self.ins_dg.set_voltage()
            i += 1


    def SetDelayBt(self):
        # Sets the value
        channel = self.ui.delay_select.currentText()
        channel_ref = self.ui.channel_link.text()
        
        #set the new channel link in case there was a change 
        self.ins_dg.change_delay_link(channel, channel_ref)
        
        #Now setting the delay
        sleep(0.2)
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.delay_select_units.currentText() != "":
            self.ins_dg.set_delay()
        
            #Then displays the change on the delay generator
            sleep(0.2)      
            self.ins_dg.change_display(channel)
        
        
    def SetVoltageBt(self):
        # Sets the value
        voltage_select = self.ui.voltage_select.currentText()
 
        sleep(0.2)
        if self.ui.offset_v.text() != "" and self.ui.amplitude_v.text() != "":
            self.ins_dg.set_voltage()
            #Then displays the change on the delay generator
            sleep(0.2)      
            self.ins_dg.display_amplitdue(voltage_select)
        
        
    def SetRelativeDelayBt(self):
        """Add or subtract a relative delay from the currently selected channel."""
        # Get the currently selected channel
        channel_key = str(self.ui.delay_select.currentText())
        
        # Get the current delay value and units for this channel
        current_delay = self.dg_values[channel_key][1]
        current_units = self.dg_values[channel_key][2]
        
        # Get the relative offset value and units from the UI
        rel_text = self.ui.rel_delay_disp.text().strip()
        if rel_text == "":
            print("Relative delay value is empty.")
            return
        
        try:
            rel_value = float(rel_text)
        except ValueError:
            print(f"Invalid relative delay value: {rel_text}")
            return
        
        rel_units = str(self.ui.rel_delay_select_units.currentText())
        direction = str(self.ui.rel_delay_select_step.currentText())  # "Increase" or "Decrease"
        
        # Convert both to seconds
        current_in_seconds = float(current_delay) * self.unit_to_seconds[current_units]
        rel_in_seconds = rel_value * self.unit_to_seconds[rel_units]
        
        # Add or subtract
        if direction == "Increase":
            new_in_seconds = current_in_seconds + rel_in_seconds
        elif direction == "Decrease":
            new_in_seconds = current_in_seconds - rel_in_seconds
        else:
            print(f"Unknown direction: {direction}")
            return
        
        # Convert back to the channel's current units
        new_delay = new_in_seconds / self.unit_to_seconds[current_units]
        
        # Update the stored value
        self.dg_values[channel_key][1] = new_delay
        
        # Update the delay display
        self.ui.delay_disp.setText(str(new_delay))
        
        # Build and send the delay command
        channel_ref = self.dg_values[channel_key][0]
        self.ins_dg.get_delay(channel_key, channel_ref, new_delay, current_units)
        
        # Set the channel link in case there was a change
        self.ins_dg.change_delay_link(channel_key, channel_ref)
        sleep(0.2)
        
        # Send the delay to the instrument
        self.ins_dg.set_delay()
        
        # Update the display on the delay generator
        sleep(0.2)
        self.ins_dg.change_display(channel_key)
        
        print(f"Relative delay applied: {direction} {rel_value} {rel_units} -> New delay: {new_delay} {current_units}")
    
    
    # Fires Delay Generator / sends a single trigger    
    def FireIns(self):
        # Check if the camera is in hardware trigger mode via the combo box
        mode = self.ui.ModeComboBox.currentText().strip()
        
        if self.cam_connected and mode == "Hardware Trigger":
            # Camera is already armed in hardware trigger mode
            # (set up by change_camera_mode when user selected Hardware Trigger)
            
            # Fire the delay generator (sends the trigger pulse)
            self.ins_dg.single_shot_fire_dg()
            
            # Capture the triggered image
            image = self.cam.capture_triggered_image(timeout_ms=5000)
            if image is not None:
                self.last_saved_image = image
                self.image_counter += 1
                self.display_camera_image(image, self.ui.CapturedImage)
                self.cam_log(f"Captured triggered image #{self.image_counter}")
            else:
                self.cam_log("Failed to capture triggered image.", is_error=True)
        else:
            # No camera connected or not in hardware trigger mode,
            # just fire the delay generator
            self.ins_dg.single_shot_fire_dg()
    
    
    def TestFireDG(self):
        """Fire the delay generator for testing. Captures and displays image but
        does NOT increment shot counter or save the image."""
        mode = self.ui.ModeComboBox.currentText().strip()
        
        if self.cam_connected and mode == "Hardware Trigger":
            # Fire the delay generator
            self.ins_dg.single_shot_fire_dg()
            
            # Capture and display only (no save, no counter increment)
            image = self.cam.capture_triggered_image(timeout_ms=5000)
            if image is not None:
                self.display_camera_image(image, self.ui.CapturedImage)
                self.cam_log("Test fire: image captured (not saved)")
            else:
                self.cam_log("Test fire: failed to capture image.", is_error=True)
        else:
            # No camera or not in hardware trigger mode, just fire
            self.ins_dg.single_shot_fire_dg()
            self.cam_log("Test fire: DG fired (no camera capture)")
    
    
    ############## XPS STAGE  FUNCTIONS ##########################
    
    # Function initialize
    def _initXPS(self):
        #Initalizing the xps
        #Initialize XPS
        try:
            self.xps_ipaddress = self.ui.ip_address_ip.text()
            self.xps = XPS(self.xps_ipaddress)
            self.xpsGroupNames = self.xps.getXPSStatus()
            self.ui.x_stage_select.clear()
            self.ui.y_stage_select.clear()
            self.ui.x_stage_select.addItems(list(self.xpsGroupNames.keys()))
            self.ui.y_stage_select.addItems(list(self.xpsGroupNames.keys()))
            self.ui.y_stage_select.setCurrentIndex(1)
            self.xpsAxes = [self.ui.x_stage_select.currentText(), self.ui.y_stage_select.currentText()]
            self.xps.setGroup(self.xpsAxes[0])
            self.xps.setGroup(self.xpsAxes[1])
            self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
            self.ui.home_xps_bt.setEnabled(True)
            self.ui.enable_dis_xps_bt.setEnabled(True)
            self.ui.init_xps_bt.setEnabled(True)
            self.ui.stop_bt.setEnabled(True)
         
            
            #Selecting the different stages
            self.ui.x_stage_select.currentIndexChanged.connect(lambda: self.updateGroup(0))
            self.ui.y_stage_select.currentIndexChanged.connect(lambda: self.updateGroup(1))
        
        except AttributeError:
            print("Error!")
            self.xps = None
        #GUI Interface
        self.updateGUIStatus()
        
    
    # Function to update the x and y info 
    def updateGroup(self, axis):
        if axis == 0:
            self.xpsAxes[0] = self.ui.x_stage_select.currentText()
            self.xps.setGroup(self.xpsAxes[0])
        if axis == 1:
            self.xpsAxes[1] = self.ui.y_stage_select.currentText()
            self.xps.setGroup(self.xpsAxes[1])
        
        self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
        self.updateGUIStatus()
    
    # Functions that corresponds to the intialize, home and enable / disable fcns
    def xpsStatusBtn(self,btn):
        if btn == "Initialize":
            print(self.xps)
            self.xps.initializeStage(str(self.xpsAxes[0]))
            self.xps.initializeStage(self.xpsAxes[1])
        elif btn == "Home":
            self.xps.homeStage(self.xpsAxes[0])
            self.xps.homeStage(self.xpsAxes[1])
        elif btn == "EnableDisable" and self.xpsStageStatus[0].upper() == "Disabled state".upper():
            self.xps.enableGroup(self.xpsAxes[0])
            self.xps.enableGroup(self.xpsAxes[1])
        elif btn == "EnableDisable" and self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
            self.xps.disableGroup(self.xpsAxes[0])
            self.xps.disableGroup(self.xpsAxes[1])
            
        self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
        self.updateGUIStatus()
        
    
    def updateMovementMode(self):

        
        # Check whether stages are ready (motion buttons should only be active if ready)
        ready = False
        if self.xps and hasattr(self, 'xpsStageStatus'):
            if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                ready = True
        
        # Independent-mode widgets
        self.ui.x_abs_mv_bt.setEnabled(ready)
        self.ui.x_step_f_bt.setEnabled(ready)
        self.ui.x_step_b_bt.setEnabled(ready)
        self.ui.y_abs_mv_bt.setEnabled(ready)
        self.ui.y_step_f_bt.setEnabled(ready)
        self.ui.y_step_b_bt.setEnabled(ready)
        self.ui.x_abs_mv_ck.setEnabled(1)
        self.ui.y_abs_mv_ck.setEnabled(1)
        


    # XPS Motion Control

    def xpsMotionBtn(self, btn):
        posX_current = float(self.xps.getStagePosition(self.xpsAxes[0]))
        posY_current = float(self.xps.getStagePosition(self.xpsAxes[1]))
        
        posX_abs = float(self.ui.x_abs_mv_ip.text())
        posY_abs = float(self.ui.y_abs_mv_ip.text())
        
        posX_rel = float(self.ui.x_step_ip.text())
        posY_rel = float(self.ui.y_step_ip.text())
        
        limit_max_x = float(self.ui.x_max_trav_ip.text())
        limit_min_x = float(self.ui.x_min_trav_ip.text())
        
        limit_max_y = float(self.ui.y_max_trav_ip.text())
        limit_min_y = float(self.ui.y_min_trav_ip.text())
        
        if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
            if btn == "AbsoluteX" and self.ui.x_abs_mv_ck.isChecked():
                if posX_abs < limit_min_x or posX_abs > limit_max_x:
                    error_msg = f"X-axis absolute move failed: Target position {posX_abs:.2f} mm is outside travel limits [{limit_min_x:.2f}, {limit_max_x:.2f}] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_x.setText('Position out of range')                  
                else:
                    self.xps.moveAbsolute(self.xpsAxes[0],posX_abs)
                    self.ui.status_label_x.setText('')
                    self.clear_error_message()
                self.updatePosition()
            elif btn == "ForwardX":
                if (posX_rel+posX_current) < limit_min_x or (posX_current+posX_rel) > limit_max_x:
                    new_pos = posX_current + posX_rel
                    error_msg = f"X-axis forward step failed: New position {new_pos:.2f} mm would exceed travel limits [{limit_min_x:.2f}, {limit_max_x:.2f}] mm. Current position: {posX_current:.2f} mm, Step: {posX_rel:.2f} mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_x.setText('Step exceeds limits')                 
                else:
                    self.xps.moveRelative(self.xpsAxes[0],posX_rel)
                    self.ui.status_label_x.setText('')
                    self.clear_error_message()
                self.updatePosition()
                
            elif btn == "BackwardX":
                if (posX_current-posX_rel) < limit_min_x or (posX_current-posX_rel) > limit_max_x:
                    new_pos = posX_current - posX_rel
                    error_msg = f"X-axis backward step failed: New position {new_pos:.2f} mm would exceed travel limits [{limit_min_x:.2f}, {limit_max_x:.2f}] mm. Current position: {posX_current:.2f} mm, Step: {posX_rel:.2f} mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_x.setText('Step exceeds limits')                  
                else:
                    self.xps.moveRelative(self.xpsAxes[0],-1*posX_rel)
                    self.ui.status_label_x.setText('')
                    self.clear_error_message()
                self.updatePosition()
                
        if self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
            if btn == "AbsoluteY" and self.ui.y_abs_mv_ck.isChecked():
                if posY_abs < limit_min_y or posY_abs > limit_max_y:
                    error_msg = f"Y-axis absolute move failed: Target position {posY_abs:.2f} mm is outside travel limits [{limit_min_y:.2f}, {limit_max_y:.2f}] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_y.setText('Position out of range')                  
                else:
                    self.xps.moveAbsolute(self.xpsAxes[1],posY_abs)
                    self.ui.status_label_y.setText('')
                    self.clear_error_message()
                self.updatePosition()
            elif btn == "ForwardY":
                if (posY_current+posY_rel) < limit_min_y or (posY_current+posY_rel) > limit_max_y:
                    new_pos = posY_current + posY_rel
                    error_msg = f"Y-axis forward step failed: New position {new_pos:.2f} mm would exceed travel limits [{limit_min_y:.2f}, {limit_max_y:.2f}] mm. Current position: {posY_current:.2f} mm, Step: {posY_rel:.2f} mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_y.setText('Step exceeds limits')                   
                else:
                    self.xps.moveRelative(self.xpsAxes[1],posY_rel)
                    self.ui.status_label_y.setText('')
                    self.clear_error_message()
                self.updatePosition()
                
            elif btn == "BackwardY":
                if (posY_current-posY_rel) < limit_min_y or (posY_current-posY_rel) > limit_max_y:
                    new_pos = posY_current - posY_rel
                    error_msg = f"Y-axis backward step failed: New position {new_pos:.2f} mm would exceed travel limits [{limit_min_y:.2f}, {limit_max_y:.2f}] mm. Current position: {posY_current:.2f} mm, Step: {posY_rel:.2f} mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_y.setText('Step exceeds limits')                   
                else:
                    self.xps.moveRelative(self.xpsAxes[1],-1*posY_rel)
                    self.ui.status_label_y.setText('')
                    self.clear_error_message()
                self.updatePosition()

        #GUI Interface
        self.updateGUIStatus()
    
    
    ## XPS Stage Combined Fcns
    
    def updateGUIStatus(self):
        if self.xps:
            if self.xpsStageStatus[0] == "Not initialized state" or self.xpsStageStatus[0] == "Not initialized state due to a GroupKill or KillAll command":
                self.ui.home_xps_bt.setEnabled(False)
                self.ui.enable_dis_xps_bt.setEnabled(False)
                self.ui.x_abs_mv_bt.setEnabled(False)
                self.ui.x_step_f_bt.setEnabled(False)
                self.ui.x_step_b_bt.setEnabled(False)
                self.ui.y_abs_mv_bt.setEnabled(False)
                self.ui.y_step_f_bt.setEnabled(False)
                self.ui.y_step_b_bt.setEnabled(False)
                self.ui.x_status.setText("Not Initialized")
                self.ui.y_status.setText("Not Initialized")
                
            elif self.xpsStageStatus[0] == "Not referenced state":
                self.ui.home_xps_bt.setEnabled(True)
                self.ui.enable_dis_xps_bt.setEnabled(False)
                self.ui.x_abs_mv_bt.setEnabled(False)
                self.ui.x_step_f_bt.setEnabled(False)
                self.ui.x_step_b_bt.setEnabled(False)
                self.ui.y_abs_mv_bt.setEnabled(False)
                self.ui.y_step_f_bt.setEnabled(False)
                self.ui.y_step_b_bt.setEnabled(False)
                self.ui.x_status.setText("Not Homed")
                self.ui.y_status.setText("Not Homed")
                
            elif self.xpsStageStatus[0] == "Disabled state":
                self.ui.enable_dis_xps_bt.setEnabled(True)
                self.ui.init_xps_bt.setEnabled(False)
                self.ui.home_xps_bt.setEnabled(False)
                self.ui.x_abs_mv_bt.setEnabled(False)
                self.ui.x_step_f_bt.setEnabled(False)
                self.ui.x_step_b_bt.setEnabled(False)
                self.ui.y_abs_mv_bt.setEnabled(False)
                self.ui.y_step_f_bt.setEnabled(False)
                self.ui.y_step_b_bt.setEnabled(False)
                self.ui.x_status.setText("Disabled")
                self.ui.y_status.setText("Disabled")
                
            elif self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                self.ui.enable_dis_xps_bt.setEnabled(True)
                self.ui.init_xps_bt.setEnabled(False)
                self.ui.home_xps_bt.setEnabled(False)
                self.ui.x_status.setText("Enabled")
                self.ui.y_status.setText("Enabled")
                # Delegate motion button enable/disable to the movement mode handler
                self.updateMovementMode()
                   
        self.updatePosition()
    
    
    def updatePosition(self):
        if self.xps:
            self.ui.x_pos_disp.setText(str(self.xps.getStagePosition(self.xpsAxes[0])))         
            self.ui.y_pos_disp.setText(str(self.xps.getStagePosition(self.xpsAxes[1])))
            self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
     
    
    def updateTravelLimits(self, lim):
        time.sleep(.5)
        if lim == "minXPSX":   
            try:
                limit = float(self.ui.x_min_trav_ip.text())
                if limit < 0 or limit > 50:
                    error_msg = f"X-axis minimum limit invalid: {limit:.2f} mm is outside allowed range [0, 50] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_x.setText('Invalid minimum limit')
                    self.ui.x_min_trav_ip.setText(str(self.xps.getminLimit(self.xpsAxes[0])))
                else:
                    self.xps.setminLimit(self.xpsAxes[0],limit)
                    self.clear_error_message()
            except:
                pass
            
        elif lim == "maxXPSX":
            try:
                limit = float(self.ui.x_max_trav_ip.text())
                if limit < 0 or limit > 50:
                    error_msg = f"X-axis maximum limit invalid: {limit:.2f} mm is outside allowed range [0, 50] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_x.setText('Invalid maximum limit')
                    self.ui.x_max_trav_ip.setText(str(self.xps.getmaxLimit(self.xpsAxes[0])))
                else:
                    self.xps.setmaxLimit(self.xpsAxes[0],limit)
                    self.clear_error_message()
            except:
                pass
            
        elif lim == "minXPSY":
            try:
                limit = float(self.ui.y_min_trav_ip.text())
                if limit < 0 or limit > 50:
                    error_msg = f"Y-axis minimum limit invalid: {limit:.2f} mm is outside allowed range [0, 50] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_y.setText('Invalid minimum limit')
                    self.ui.y_min_trav_ip.setText(str(self.xps.getminLimit(self.xpsAxes[1])))
                else:
                    self.xps.setminLimit(self.xpsAxes[1],limit)
                    self.clear_error_message()
            except:
                pass
            
        elif lim == "maxXPSY":
            try:
                limit = float(self.ui.z_max_trav_ip.text())
                if limit < 0 or limit > 50:
                    error_msg = f"Y-axis maximum limit invalid: {limit:.2f} mm is outside allowed range [0, 50] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_y.setText('Invalid maximum limit')
                    self.ui.y_max_trav_ip.setText(str(self.xps.getmaxLimit(self.xpsAxes[1])))
                else:
                    self.xps.setmaxLimit(self.xpsAxes[1],limit)
                    self.clear_error_message()
            except:
                pass
        
    

        
    ### CAMERA METHODS #######
    
    def cam_log(self, message, is_error=False):
        """Log a camera message to the GUI display, and to the terminal only for errors."""
        if is_error:
            print(message)
        self.ui.cam_disp_messages.setText(str(message))
    
    def find_cameras_btn(self):
        """Find available FLIR cameras and populate the combo box."""
        try:
            serials = self.cam.find_cameras()
            if not serials:
                self.cam_log("No FLIR cameras found.")
                return
            self.ui.Found_Cam_ComboBox.clear()
            for serial in serials:
                self.ui.Found_Cam_ComboBox.addItem(serial)
            self.cam_log(f"Found {len(serials)} camera(s): {serials}")
        except Exception as e:
            self.cam_log(f"Error finding cameras: {e}", is_error=True)
    
    def connect_camera(self):
        """Connect to the camera selected in Found_Cam_ComboBox."""
        selected_serial = self.ui.Found_Cam_ComboBox.currentText()
        if not selected_serial:
            self.cam_log("No camera selected. Click 'Find' first.")
            return
        try:
            if self.cam_connected:
                self.disconnect_camera()
            self.cam.connect(selected_serial)
            self.cam_connected = True
            self.change_camera_mode()
            self.cam_log(f"Camera connected: {selected_serial}")
        except Exception as e:
            self.cam_log(f"Error connecting to camera: {e}", is_error=True)
    
    def start_video(self):
        """Start the live video feed."""
        if not self.cam_connected:
            self.cam_log("No camera connected.")
            return
        if self.cam.trigger_mode != "continuous":
            self.cam.configure_continuous()
            self.ui.ModeComboBox.setCurrentIndex(0)
        self.cam.start_acquisition()
        self.video_running = True
        self.video_timer.start(33)  # ~30 fps
        self.cam_log("Live video started.")
    
    def stop_video(self):
        """Stop the live video feed."""
        self.video_running = False
        self.video_timer.stop()
        if self.cam_connected and self.cam.is_acquiring:
            self.cam.stop_acquisition()
        self.cam_log("Live video stopped.")
    
    def update_video_feed(self):
        """Timer callback: grab a frame and display it in the live feed."""
        if not self.cam_connected or not self.video_running:
            return
        image = self.cam.get_image(timeout_ms=1000)
        if image is not None:
            self.display_camera_image(image, self.ui.CapturedImage)
    
    def change_camera_mode(self):
        """Handle camera mode change from the ModeComboBox."""
        if not self.cam_connected:
            return
        if self.video_running:
            self.stop_video()
        mode = self.ui.ModeComboBox.currentText().strip()
        if mode in ("Continous", "Continuous"):
            self.cam.configure_continuous()
        elif "Hardware Trigger" in mode:
            self.cam.configure_trigger(source="hardware")
            self.cam.start_acquisition()
            self.cam_log("Camera armed for hardware trigger. Fire the delay generator to capture.")
    
    def disconnect_camera(self):
        """Disconnect the camera and clean up."""
        if self.video_running:
            self.stop_video()
        if self.cam_connected:
            self.cam.disconnect()
            self.cam_connected = False
            self.cam_log("Camera disconnected.")
    
    def apply_exposure_time(self):
        """Read the exposure time input, send to camera, update with actual value."""
        if not self.cam_connected:
            self.cam_log("No camera connected.")
            return
        text = self.ui.exposure_time_ip.text().strip()
        if not text:
            return
        try:
            requested_us = float(text)
        except ValueError:
            self.cam_log("Invalid exposure time. Enter a number in us.", is_error=True)
            return
        try:
            actual_us = self.cam.set_exposure(requested_us)
            self.ui.exposure_time_ip.setText(f"{actual_us:.1f}")
            self.cam_log(f"Exposure set to {actual_us:.1f} us")
        except Exception as e:
            self.cam_log(f"Error setting exposure: {e}", is_error=True)
    
    def apply_gain(self):
        """Read the gain input, send to camera, update with actual value."""
        if not self.cam_connected:
            self.cam_log("No camera connected.")
            return
        text = self.ui.gain_ip.text().strip()
        if not text:
            return
        try:
            requested_db = float(text)
        except ValueError:
            self.cam_log("Invalid gain. Enter a number in dB.", is_error=True)
            return
        try:
            actual_db = self.cam.set_gain(requested_db)
            self.ui.gain_ip.setText(f"{actual_db:.2f}")
            self.cam_log(f"Gain set to {actual_db:.2f} dB")
        except Exception as e:
            self.cam_log(f"Error setting gain: {e}", is_error=True)
    
    def selectSaveDirectory(self):
        """Open a file dialog to select the directory for saving all data."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Save Directory",
            self.save_directory,  # Start at the current save directory
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if directory:
            self.save_directory = directory
            self.ui.raster_overview_disp_2.setText(f"Save directory: {self.save_directory}")
            self.cam_log(f"Save directory set to: {self.save_directory}")
    
    def save_captured_image_btn(self):
        """Save the last captured image with a filename based on image counter and EF delay."""
        if self.last_saved_image is None:
            self.cam_log("No captured image to save.")
            return
        os.makedirs(self.save_directory, exist_ok=True)
        delay_val = str(self.dg_values["E"][1])
        delay_unit = str(self.dg_values["E"][2])
        delay_str = delay_val.replace(".", "-")
        filename = f"test_{self.image_counter}_chE_{delay_str}_{delay_unit}.bmp"
        filepath = os.path.join(self.save_directory, filename)
        self.save_camera_image(self.last_saved_image, filepath)
    
    def display_camera_image(self, image_array, image_view):
        """Display a numpy image array on a pyqtgraph ImageView widget."""
        image_view.setImage(
            image_array.T,
            autoRange=not self.video_running,
            autoLevels=not self.video_running
        )
    
    def save_camera_image(self, image_array, filepath):
        """Save a numpy image array to a file."""
        cv2.imwrite(filepath, image_array)
        self.cam_log(f"Image saved to {filepath}")

    ### COMBINED FCNS #######
    
    def StartScan(self):
        """Execute the full raster scan with time-resolved shadowgraphy."""
        
        # First check if the scan parameters have been set
        # (SetScanParam already validates T0 and save directory)
        if not hasattr(self, 'total_scan_shots') or not hasattr(self, 'scan_time_steps'):
            self.display_error_message("Set scan parameters first.", "ERROR")
            return
        
        # Then check if the XPS has been enabled
        if not self.xps or not hasattr(self, 'xpsStageStatus'):
            self.display_error_message("Connect and enable XPS stages first.", "ERROR")
            return
        if self.xpsStageStatus[0][:11].upper() != "Ready state".upper():
            self.display_error_message("XPS stages are not in Ready state.", "ERROR")
            return
        
        # Then check if the camera is connected and in hardware trigger mode
        if not self.cam_connected:
            self.display_error_message("Connect camera first.", "ERROR")
            return
        mode = self.ui.ModeComboBox.currentText().strip()
        if mode != "Hardware Trigger":
            self.display_error_message("Set camera to Hardware Trigger mode first.", "ERROR")
            return
        
        # --- Raster scan setup ---
        # Convert shot separation from meters to mm (XPS positions are in mm)
        shot_sep_mm = self.shot_sep 
        # Determine step directions
        y_step = shot_sep_mm if self.y_stop >= self.y_start else -shot_sep_mm
        x_step = shot_sep_mm if self.x_stop >= self.x_start else -shot_sep_mm
        
        # Calculate total number of steps across the full target area
        total_y_steps = int(abs(self.y_stop - self.y_start) / shot_sep_mm) + 1
        total_x_steps = int(abs(self.x_stop - self.x_start) / shot_sep_mm) + 1
        print(total_x_steps)
        # Determine starting position and Y direction
        # If we have a resume position from a previous scan, use that
        if self.scan_resume_pos is not None:
            scan_x_start = self.scan_resume_pos['x']
            scan_y_start = self.scan_resume_pos['y']
            y_direction = self.scan_resume_pos['y_dir']
            start_ix = self.scan_resume_pos['ix']
        else:
            scan_x_start = self.x_start
            scan_y_start = self.y_start
            y_direction = 1
            start_ix = 0
        
        # Calculate how many X columns remain from the resume point
        num_x_remaining = total_x_steps - start_ix
        
        # Calculate how many positions we need for this scan
        # (shots per position = shots_per_time_step * num_time_steps)
        shots_per_position = self.shot_per_time_step * len(self.scan_time_steps)
        positions_needed = int(np.ceil(self.total_scan_shots / shots_per_position))
        positions_available = num_x_remaining * total_y_steps
        
        if positions_available <= 0:
            self.display_error_message("Target area exhausted. Set new start/stop positions.", "ERROR")
            self.scan_resume_pos = None
            return
        
        # Move to the starting position using relative moves
        try:
            x_current = float(self.xps.getStagePosition(self.xpsAxes[0]))
            y_current = float(self.xps.getStagePosition(self.xpsAxes[1]))
            
            dx_start = scan_x_start - x_current
            dy_start = scan_y_start - y_current
            
            if abs(dx_start) > 1e-4:
                self.xps.moveRelative(self.xpsAxes[0], dx_start)
                sleep(0.5)
            if abs(dy_start) > 1e-4:
                self.xps.moveRelative(self.xpsAxes[1], dy_start)
                sleep(0.5)
        except Exception as e:
            self.display_error_message(f"Error reading position or moving to start: {e}", "ERROR")
            return
            
        # Get the T0 channel info
        channel_key = self.t_zero_channel
        channel_ref = self.dg_values[channel_key][0]
        current_units = self.t_zero_units
        
        # Ensure save directory exists
        os.makedirs(self.save_directory, exist_ok=True)
        
        # Track overall shot number
        overall_shot = 0
        scan_complete = False
        
        # Create or append to the CSV log file for scan data
        csv_filepath = os.path.join(self.save_directory, "scan_log.csv")
        file_is_new = not os.path.exists(csv_filepath)
        
        # Test file access and write header if new
        try:
            with open(csv_filepath, 'a', newline='') as f:
                writer = csv.writer(f)
                if file_is_new:
                    writer.writerow([
                        "Shot #", "Filename", 
                        "Relative Time (s)", "Absolute Delay", "Delay Units",
                        "X Position (mm)", "Y Position (mm)",
                        "Channel"
                    ])
        except PermissionError:
            self.display_error_message(f"Permission denied: Please close 'scan_log.csv' (e.g. in Excel) before scanning.", "ERROR")
            return
        except Exception as e:
            self.display_error_message(f"Error accessing CSV: {e}", "ERROR")
            return
        
        self.display_error_message("Scan started...", "INFO")
        QtWidgets.QApplication.processEvents()
        
        # Create a flattened list of all delays needed for the scan
        delays_needed = []
        for time_offset in self.scan_time_steps:
            for _ in range(self.shot_per_time_step):
                delays_needed.append(time_offset)
                
        # --- Begin raster scan ---
        shot_idx = 0
        for ix_offset in range(num_x_remaining):
            ix = start_ix + ix_offset
            
            # Step in X (skip on first iteration, already jumped to start)
            if ix_offset > 0:
                self.xps.moveRelative(self.xpsAxes[0], x_step)
                sleep(0.3)
            
            # Determine Y traversal order for serpentine pattern
            if y_direction == 1:
                y_range = range(total_y_steps)
                step_y = y_step
            else:
                y_range = range(total_y_steps - 1, -1, -1)
                step_y = -y_step
            
            for iy_offset, iy in enumerate(y_range):
                # Move to the current Y position (Relative strategy)
                # Skip moving Y on the 0th item inside the column, because we
                # only shifted X from the previous column's last Y position!
                if iy_offset > 0:
                    self.xps.moveRelative(self.xpsAxes[1], step_y)
                    sleep(0.2)
                
                # Get the delay needed for this specific shot
                time_offset = delays_needed[shot_idx]
                
                # Calculate the absolute delay for this time step
                new_delay_seconds = self.t_zero_seconds + (self.t_zero_step_dir * time_offset)
                
                # Convert back to the channel's display units and round to 14 decimals to prevent float artifacts while preserving ps precision
                new_delay_value = round(new_delay_seconds / self.unit_to_seconds[current_units], 14)
                
                # Update the delay on the instrument
                self.dg_values[channel_key][1] = new_delay_value
                self.ins_dg.get_delay(channel_key, channel_ref, new_delay_value, current_units)
                sleep(0.2)
                self.ins_dg.set_delay()
                sleep(0.2)
                
                overall_shot += 1
                
                # 1. Fire the delay generator (triggers the camera)
                self.ins_dg.single_shot_fire_dg()
                
                # 2. Capture the triggered image
                image = self.cam.capture_triggered_image(timeout_ms=5000)
                if image is not None:
                    self.last_saved_image = image
                    self.image_counter += 1
                    self.display_camera_image(image, self.ui.CapturedImage)
                    
                    # Save with shot number and delay info
                    delay_str = str(new_delay_value).replace(".", "-")
                    filename = f"scan_{self.image_counter}_ch{channel_key}_{delay_str}_{current_units}.bmp"
                    filepath = os.path.join(self.save_directory, filename)
                    self.save_camera_image(image, filepath)
                    
                    # Log to CSV
                    x_current = float(self.xps.getStagePosition(self.xpsAxes[0]))
                    y_current = float(self.xps.getStagePosition(self.xpsAxes[1]))
                    try:
                        with open(csv_filepath, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                self.image_counter, filename,
                                time_offset, new_delay_value, current_units,
                                x_current, y_current,
                                channel_key
                            ])
                    except Exception as e:
                        self.cam_log(f"Warning: Failed to log row {self.image_counter} to CSV: {e}", is_error=True)
                else:
                    self.cam_log(f"Failed to capture image at shot {overall_shot}", is_error=True)
                
                # 3. Update status display
                self.ui.status_label.setText(
                    f"Shot {overall_shot}/{self.total_scan_shots} | "
                    f"X:{ix+1}/{total_x_steps} Y:{iy+1}/{total_y_steps}"
                )
                QtWidgets.QApplication.processEvents()
                sleep(0.1)
                
                shot_idx += 1
                
                # Check if we've taken all the shots needed
                if shot_idx >= len(delays_needed):
                    scan_complete = True
                    break
            
            # Flip Y direction for serpentine pattern
            y_direction *= -1
            
            if scan_complete:
                break
        
        # Save the resume position for the next scan
        # The next scan should start at the next unused position
        next_ix = ix + 1 if scan_complete else ix + 1
        if next_ix >= total_x_steps:
            # Target area fully exhausted
            self.scan_resume_pos = None
            self.display_error_message(
                f"Scan complete! {overall_shot} shots taken. Target area fully used.", "INFO")
        else:
            next_x = self.x_start + next_ix * x_step
            self.scan_resume_pos = {
                'x': next_x,
                'y': self.y_start,
                'y_dir': y_direction,
                'ix': next_ix
            }
            self.display_error_message(
                f"Scan complete! {overall_shot} shots taken. "
                f"Next scan resumes at X={next_x:.3f} mm (column {next_ix+1}/{total_x_steps}).", "INFO")
        
        self.ui.status_label.setText(f"Scan complete: {overall_shot} total shots")
        self.ui.ShotCounter_disp.setText(str(self.image_counter))
        
        # (CSV file was written to iteratively, no need to keep an open handle)
        self.cam_log(f"Scan log saved to {csv_filepath}")
        
        # Display the current time relative to T0
        # Use the last time_offset from the scan (in seconds)
        last_rel_time = self.scan_time_steps[-1] if self.scan_time_steps else 0
        
        # Pick the best display unit for readability
        abs_time = abs(last_rel_time)
        if abs_time == 0:
            display_val, display_unit = 0, "s"
        elif abs_time >= 1:
            display_val, display_unit = last_rel_time, "s"
        elif abs_time >= 1e-3:
            display_val, display_unit = last_rel_time / 1e-3, "ms"
        elif abs_time >= 1e-6:
            display_val, display_unit = last_rel_time / 1e-6, "us"
        elif abs_time >= 1e-9:
            display_val, display_unit = last_rel_time / 1e-9, "ns"
        else:
            display_val, display_unit = last_rel_time / 1e-12, "ps"
        
        self.ui.rel_time_disp.setText(f"{display_val:.4g}")
        self.ui.rel_time_unit_disp.setCurrentText(display_unit)
    
   
    def DisconnectBtn(self):
        #Shutting down the XPS stages 
        if self.xps:
            if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[0])
            if self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[1])
            self.updateGUIStatus()
        
        
        #Shutdown Delay generator
        # First writing the json file to save current settings
        with open(os.path.join(script_dir, "delay_gen_gui_inputs.json"), "r+") as write_file:
            inputs = json.load(write_file)
            
            for i in ["A", "B", "C", "D", "E", "F", "G", "H"]:
                inputs[i+"_ch"] = self.dg_values[i][0]
                inputs[i+"_delay"] = self.dg_values[i][1]
                inputs[i+"_delay_unit"] = self.dg_values[i][2]
            for i in ["AB", "CD", "EF", "GH"]:
                inputs[i+"_offset"] = self.dg_values[i][0]
                inputs[i+"_Amp"] = self.dg_values[i][1]
            
            # Save the current trigger source
            current_trig_src = self.ins_dg.query_trg_src()
            inputs["trigger_source"] = current_trig_src
                
            write_file.seek(0)
            json.dump(inputs, write_file)
            write_file.truncate()
            
        #Disconnecting the device now
        self.ins_dg.disconnect_dg()
        
        # Clean up camera resources
        if self.video_running:
            self.stop_video()
        if self.cam_connected:
            self.cam.disconnect()
        self.cam.release_system()
        
        #Disconnecting the app now 
        QtWidgets.QApplication.quit()
        
           

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = solid_target_stage_app_stage_app()
    application.show()
    sys.exit(app.exec_()) 