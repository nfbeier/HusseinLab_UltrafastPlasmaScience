#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 15:15:03 2025

@author: Christina Strilets
"""

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import numpy as np
import time, sys
from time import sleep
import instruments as ik
import json
import os
import socket

# Script directory for saved position files
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add FLIR Camera Code directory to path for BlackflyCamera import
flir_code_dir = os.path.join(
    script_dir, "Camera Testing", "FLIR Camera Code"
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
from Software.SolidTargetStage.prelim_solid_stage_gui import Ui_MainWindow

#Importing the Delay generator class 
from Hardware.DG645.dg645 import DelayGen

#Importing the XPS Class
from Hardware.XPS.XPS import XPS

# Connecting with the RPi first for the rotation stage
HOST = '192.168.0.106'  # Replace with Raspberry Pi's IP
PORT = 5000


#%%
class solid_target_stage_app_stage_app(QtWidgets.QMainWindow):
    def __init__(self):
        super(solid_target_stage_app_stage_app,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        ### ROTATION STAGE SETUP #######
        # Defining important values for the rotation stage
        self.shot_mode = self.ui.shot_mode_select.currentText()
        self.shot_num = int(self.ui.shot_no_ip.text())
        self.num_shot_taken = int(self.ui.shots_taken_disp.toPlainText())
        self.rep_rate = float(self.ui.rep_rate_select.currentText())
        self.ref_delay = float(self.ui.rel_delay_ip.text())*1e-3
        self.ref_delay_dg = self.ui.rel_delay_ip.text()
        self.shot_sep = float(self.ui.shot_sep_ip.text())*1e-6
        self.rpm = ''
        self.dg_delay = 0
        self.ui.single_rot_fw_ck.setEnabled(True)
        self.ui.single_rot_bw_ck.setEnabled(True)
        self.step_per_rev = 1600
        self.step_taken = 0
        
        
        #Connecting to Rpi
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))
        
        
        ### DELAY GENERATOR SETUP #######
        
        #Connecting the delay generator instrument
        self.ins_dg = DelayGen("COM4", 9600) # dg645
        
        
        ##### XPS STAGE SETUP ######
        self.xps = None
        self.xpsAxes = [None, None]
        
        # XPS GUI Setup
        self.ui.x_min_trav_ip.setText('0')
        self.ui.x_max_trav_ip.setText('46')
        
        self.ui.z_min_trav_ip.setText('0')
        self.ui.z_max_trav_ip.setText('50')
        
        self.ui.x_abs_mv_ip.setText('0')
        self.ui.z_abs_mv_ip.setText('0')
        
        self.ui.x_step_ip.setText('0')
        self.ui.z_step_ip.setText('0')
        
  
        ######### ROTATION GUI CONTROLS #########
        # Selecting the rep rate 
        self.ui.rep_rate_select.currentIndexChanged.connect(self.select_rep_rate)         
        
        # Selecting the shot mode
        self.ui.shot_mode_select.currentIndexChanged.connect(self.select_shot_mode)
       
        #Selecting the number of shots
        self.ui.shot_no_ip.textChanged.connect(self.update_shot_no)
        
        #Setting the delay for the rotation stage
        self.ui.rel_delay_ip.textChanged.connect(self.update_rot_stage_delay)
        self.ui.rel_delay_set_bt.clicked.connect(self.RelDelayBtn)
        
        #Adjusting and updating effective separation between shots
        self.ui.shot_sep_ip.textChanged.connect(self.updateEffSep)
                        
        #Adjusting and updating rotation stage diameter
        self.ui.target_diam_ip.textChanged.connect(self.updateDiameter)
        
        # Calculating the RPM button
        self.ui.rpm_bt.clicked.connect(self.CalculateRPMButton)
        
        
        
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
        self.ui.delay_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Val"))
        self.ui.unit_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Units"))
        
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
        
        self.ui.z_min_trav_ip.textChanged.connect(lambda: self.updateTravelLimits("minXPSZ"))
        self.ui.z_min_trav_ip.textChanged.connect(lambda: self.updateTravelLimits("maxXPSZ"))
        
        #Moving the two stages
        self.ui.x_abs_mv_bt.clicked.connect(lambda: self.xpsMotionBtn("AbsoluteX"))
        self.ui.x_step_f_bt.clicked.connect(lambda: self.xpsMotionBtn("ForwardX"))
        self.ui.x_step_b_bt.clicked.connect(lambda: self.xpsMotionBtn("BackwardX"))
        
        self.ui.z_abs_mv_bt.clicked.connect(lambda: self.xpsMotionBtn("AbsoluteZ"))
        self.ui.z_step_f_bt.clicked.connect(lambda: self.xpsMotionBtn("ForwardZ"))
        self.ui.z_step_b_bt.clicked.connect(lambda: self.xpsMotionBtn("BackwardZ"))
        
        #Moving together buttons
        self.ui.abs_mv_together_bt.clicked.connect(lambda: self.xpsMotionBtn("AbsoluteTogether"))
        self.ui.step_fwd_together_bt.clicked.connect(lambda: self.xpsMotionBtn("ForwardTogether"))
        self.ui.step_bckwd_together_bt.clicked.connect(lambda: self.xpsMotionBtn("BackwardTogether"))
        
        #Movement mode combo box
        self.ui.stage_movement_select.currentIndexChanged.connect(self.updateMovementMode)
        
        # Start in independent mode — disable together widgets
        self.updateMovementMode()
        
        #Save and recall position buttons (two experiments: objective and target)
        self.saved_positions_files = {
            "objective": os.path.join(script_dir, "saved_positions_objective.json"),
            "target": os.path.join(script_dir, "saved_positions_target.json")
        }
        self._initSavedPositions()
        self.ui.save_current_pos_obj_bt.clicked.connect(lambda: self.savePosition("objective"))
        self.ui.recall_obj_saved_bt.clicked.connect(lambda: self.recallPosition("objective"))
        self.ui.save_current_pos_target_bt.clicked.connect(lambda: self.savePosition("target"))
        self.ui.recall_target_saved_bt.clicked.connect(lambda: self.recallPosition("target"))
        
        
        ####### CAMERA SETUP ########
        self.cam = BlackflyCamera()
        self.cam_connected = False
        self.video_running = False
        self.last_saved_image = None
        self.image_counter = 0
        
        # Hide ROI and menu buttons on the promoted ImageView widgets
        self.ui.LiveFeedLabel.ui.roiBtn.hide()
        self.ui.LiveFeedLabel.ui.menuBtn.hide()
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
        # Setting the Start Button
        self.ui.fire_dg_bt.clicked.connect(self.StartRot)
        
        #Setting the  disconnect
        self.ui.stop_bt.clicked.connect(self.DisconnectBtn)
        
        # Initialize error message label
        self.ui.error_msg_label.setText('')
        # self.ui.error_msg_label.setStyleSheet("color: red;") # Removed initial color setting
        
        
        
        
    ######### ROTATION FUNCTIONS #########  
    
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
    
    def select_rep_rate(self):   
        self.rep_rate = float(self.ui.rep_rate_select.currentText())
        if self.num_shot_taken == 0:
            self.ui.shots_left_disp.setText(str(self.shot_per_rot))

    def select_shot_mode(self):    
        self.shot_mode = self.ui.shot_mode_select.currentText()
        if self.shot_mode == 'Single Rotation':
            self.ui.single_rot_fw_ck.setEnabled(True)
            self.ui.single_rot_bw_ck.setEnabled(True)
        else:
            self.ui.single_rot_fw_ck.setEnabled(False)
            self.ui.single_rot_bw_ck.setEnabled(False)
            
    
    def updateEffSep(self):   
        self.shot_sep_prelim = self.ui.shot_sep_ip.text()
        if  self.shot_sep_prelim != '':
            self.shot_sep = float(self.shot_sep_prelim)*1e-6
            
    
    def update_shot_no(self):   
        shot_num_text = self.ui.shot_no_ip.text()
        if shot_num_text != '':
            self.shot_num = int(shot_num_text)
            self.updateStep4Shot()
            
    def updateStep4Shot(self):
        # Parameters needed to calculate the step # given
        # the shot #
        self.step_num = 0
        self.step_num_text = ''
        self.sep = self.shot_sep
        self.diam_target = self.ui.target_diam_ip.text()
        
        if self.shot_num == 1:
            self.step_num = 1
            self.ui.step_4_shot_disp.setText(str(self.step_num))
        elif self.diam_target != '': 
            self.radius = float(self.diam_target) * 0.5
            
            # Calculating how many shots one can take in one rotation 
            self.shot_per_rot = int((2*np.pi*self.radius*1e-3)/(self.sep))
            
            # Calculating the steps needed to take for given shot #
            self.step_num = ((self.shot_num / self.shot_per_rot) * self.step_per_rev)
            
            # Displaying the results 
            self.step_num_text = f"{self.step_num:.2f}"
            self.ui.step_4_shot_disp.setText(self.step_num_text)
                   
        
    def update_rot_stage_delay(self):
        self.ref_delay_dg = self.ui.rel_delay_ip.text()
        if self.ref_delay_dg != '':
            self.ref_delay = float(self.ref_delay_dg)*1e-3
    
    def updateDiameter(self):
        self.diam_target = self.ui.target_diam_ip.text()
    
    def RelDelayBtn(self):
        self.ref_delay_dg = self.ui.rel_delay_ip.text()
        self.ref_delay = float(self.ref_delay_dg)*1e-3
    
    def CalculateRPMButton(self):
        """Wrapper function for the Calculate RPM button that also sets delay generator"""
        self.CalculateRPM()
        if self.rpm != '':
            self.setDelaysDG()
        
    def CalculateRPM(self):
        #Parameters needed to calculate the rpm
        self.sep = self.shot_sep
        self.diam_target = str(self.ui.target_diam_ip.text())
        rep_rate = float(self.ui.rep_rate_select.currentText()) 
        if (self.diam_target != ''): 
            self.radius = float(self.diam_target) * 0.5
            self.rpm = (self.sep/(self.radius*1e-3))*(1/(2*np.pi))*60*1000*rep_rate
            
            # Calculating how many shots one can take in one rotation 
            self.shot_per_rot = int((2*np.pi*self.radius*1e-3)/(self.sep))
            
            # Calculating the shots of steps taken in a single step
            self.shot_per_step = (1/self.step_per_rev)*((2*np.pi*self.radius*1e-3)/(self.sep))
            
            # Calculating the frequency for delay calculations
            self.freq = self.rpm * self.step_per_rev * (1/60)
            self.delay_value_rot = (1/self.freq) * 0.5
            
            # Seeing if the rpm is too high
            # based off the maximum recommended working speed not 
            # max allowable speed for a NEMA 23 stepper motor
            if self.rpm > 500:
                error_msg = f"RPM calculation failed: Calculated RPM ({self.rpm:.2f}) exceeds motor maximum (500 RPM). Reduce shot separation or target diameter."
                self.display_error_message(error_msg, "ERROR")
                self.ui.status_label.setText("RPM too high for motor")
                self.rpm = ''
            else:
                self.rpm = str(self.rpm)
                self.clear_error_message()


        
    def updateShotNo(self):
        if (self.step_num+ self.step_taken) <= self.step_per_rev:
            self.step_taken = self.step_taken + self.step_num
            self.num_shot_taken = self.num_shot_taken+int(self.shot_per_step*self.step_num)
            self.shot_left = self.shot_per_rot - self.num_shot_taken
            self.step_taken = int(self.step_taken)
            #Updating the UI
            self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
            self.ui.progressBar.setValue(self.step_taken)
            self.ui.steps_taken_disp.setText(str(self.step_taken))
            
            # Seeing if a rotation has been completed 
            # Get the current value
            current_value = float(self.ui.progressBar.value())
            if current_value == float(self.step_per_rev):
                #Telling the user the stage has completed a 
                # full rotation and to step forward
                self.ui.status_label.setText("Full Rotation Complete, Move the Stage")
            

        
     
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
            self.ui.delay_disp.setText(str(self.dg_values[channel][1]))   
            self.ui.unit_disp.setText(self.dg_values[channel][2])
            
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
        self.ui.channel_link.setText(self.dg_values[channel][0])      
        if widget == "Delay_Val" and (self.ui.delay_disp.text() != ''):
            delay = float(self.ui.delay_disp.text())
            self.dg_values[channel][1] = delay
        elif widget == "Delay_Units" and (self.ui.unit_disp.text() != ''):
            delay_units = self.ui.unit_disp.text()
            self.dg_values[channel][2] = delay_units
         
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.unit_disp.text() != "":
            channel_ref = self.ui.channel_link.text()
            delay = float(self.ui.delay_disp.text())
            delay_units = self.ui.unit_disp.text()
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
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.unit_disp.text() != "":
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
            self.ui.z_stage_select.clear()
            self.ui.x_stage_select.addItems(list(self.xpsGroupNames.keys()))
            self.ui.z_stage_select.addItems(list(self.xpsGroupNames.keys()))
            self.ui.z_stage_select.setCurrentIndex(1)
            self.xpsAxes = [self.ui.x_stage_select.currentText(), self.ui.z_stage_select.currentText()]
            
            self.xps.setGroup(self.xpsAxes[0])
            self.xps.setGroup(self.xpsAxes[1])
            self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
            
            self.ui.home_xps_bt.setEnabled(True)
            self.ui.enable_dis_xps_bt.setEnabled(True)
            self.ui.init_xps_bt.setEnabled(True)
            self.ui.stop_bt.setEnabled(True)
            self.ui.save_current_pos_obj_bt.setEnabled(True)
            self.ui.recall_obj_saved_bt.setEnabled(True)
            self.ui.save_current_pos_target_bt.setEnabled(True)
            self.ui.recall_target_saved_bt.setEnabled(True)
            
            #Selecting the different stages
            self.ui.x_stage_select.currentIndexChanged.connect(lambda: self.updateGroup(0))
            self.ui.z_stage_select.currentIndexChanged.connect(lambda: self.updateGroup(1))
            
        except AttributeError:
            self.xps = None
        #GUI Interface
        self.updateGUIStatus()
        
    
    # Function to update the x and z info 
    def updateGroup(self, axis):
        if axis == 0:
            self.xpsAxes[0] = self.ui.x_stage_select.currentText()
            self.xps.setGroup(self.xpsAxes[0])
        if axis == 1:
            self.xpsAxes[1] = self.ui.z_stage_select.currentText()
            self.xps.setGroup(self.xpsAxes[1])
        
        self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
        self.updateGUIStatus()
    
    # Functions that corresponds to the intialize, home and enable / disable fcns
    def xpsStatusBtn(self,btn):
        if btn == "Initialize":
            self.xps.initializeStage(self.xpsAxes[0])
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
        """Enable/disable widgets based on the selected movement mode."""
        mode = self.ui.stage_movement_select.currentIndex()  # 0 = independent, 1 = together
        independent = (mode == 0)
        together = (mode == 1)
        
        # Check whether stages are ready (motion buttons should only be active if ready)
        ready = False
        if self.xps and hasattr(self, 'xpsStageStatus'):
            if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                ready = True
        
        # Independent-mode widgets
        self.ui.x_abs_mv_bt.setEnabled(independent and ready)
        self.ui.x_step_f_bt.setEnabled(independent and ready)
        self.ui.x_step_b_bt.setEnabled(independent and ready)
        self.ui.z_abs_mv_bt.setEnabled(independent and ready)
        self.ui.z_step_f_bt.setEnabled(independent and ready)
        self.ui.z_step_b_bt.setEnabled(independent and ready)
        self.ui.x_abs_mv_ck.setEnabled(independent)
        self.ui.z_abs_mv_ck.setEnabled(independent)
        
        # Together-mode widgets
        self.ui.abs_mv_together_bt.setEnabled(together and ready)
        self.ui.step_fwd_together_bt.setEnabled(together and ready)
        self.ui.step_bckwd_together_bt.setEnabled(together and ready)
        self.ui.together_abs_mv_ck.setEnabled(together)

    # XPS Motion Control

    def xpsMotionBtn(self, btn):
        posX_current = float(self.xps.getStagePosition(self.xpsAxes[0]))
        posZ_current = float(self.xps.getStagePosition(self.xpsAxes[1]))
        
        posX_abs = float(self.ui.x_abs_mv_ip.text())
        posZ_abs = float(self.ui.z_abs_mv_ip.text())
        
        posX_rel = float(self.ui.x_step_ip.text())
        posZ_rel = float(self.ui.z_step_ip.text())
        
        limit_max_x = float(self.ui.x_max_trav_ip.text())
        limit_min_x = float(self.ui.x_min_trav_ip.text())
        
        limit_max_z = float(self.ui.z_max_trav_ip.text())
        limit_min_z = float(self.ui.z_min_trav_ip.text())
        
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
            if btn == "AbsoluteZ" and self.ui.z_abs_mv_ck.isChecked():
                if posZ_abs < limit_min_z or posZ_abs > limit_max_z:
                    error_msg = f"Z-axis absolute move failed: Target position {posZ_abs:.2f} mm is outside travel limits [{limit_min_z:.2f}, {limit_max_z:.2f}] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_z.setText('Position out of range')                  
                else:
                    self.xps.moveAbsolute(self.xpsAxes[1],posZ_abs)
                    self.ui.status_label_z.setText('')
                    self.clear_error_message()
                self.updatePosition()
            elif btn == "ForwardZ":
                if (posZ_current+posZ_rel) < limit_min_z or (posZ_current+posZ_rel) > limit_max_z:
                    new_pos = posZ_current + posZ_rel
                    error_msg = f"Z-axis forward step failed: New position {new_pos:.2f} mm would exceed travel limits [{limit_min_z:.2f}, {limit_max_z:.2f}] mm. Current position: {posZ_current:.2f} mm, Step: {posZ_rel:.2f} mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_z.setText('Step exceeds limits')                   
                else:
                    self.xps.moveRelative(self.xpsAxes[1],posZ_rel)
                    self.ui.status_label_z.setText('')
                    self.clear_error_message()
                self.updatePosition()
                
            elif btn == "BackwardZ":
                if (posZ_current-posZ_rel) < limit_min_z or (posZ_current-posZ_rel) > limit_max_z:
                    new_pos = posZ_current - posZ_rel
                    error_msg = f"Z-axis backward step failed: New position {new_pos:.2f} mm would exceed travel limits [{limit_min_z:.2f}, {limit_max_z:.2f}] mm. Current position: {posZ_current:.2f} mm, Step: {posZ_rel:.2f} mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_z.setText('Step exceeds limits')                   
                else:
                    self.xps.moveRelative(self.xpsAxes[1],-1*posZ_rel)
                    self.ui.status_label_z.setText('')
                    self.clear_error_message()
                self.updatePosition()

        # --- Together mode: move both axes simultaneously ---
        if self.xpsStageStatus[0][:11].upper() == "Ready state".upper() and self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
            if btn == "AbsoluteTogether" and self.ui.together_abs_mv_ck.isChecked():
                x_ok = limit_min_x <= posX_abs <= limit_max_x
                z_ok = limit_min_z <= posZ_abs <= limit_max_z
                if not x_ok or not z_ok:
                    error_msg = "Together absolute move failed: One or both target positions are outside travel limits"
                    self.display_error_message(error_msg, "ERROR")
                else:
                    self.xps.moveAbsolute(self.xpsAxes[0], posX_abs)
                    self.xps.moveAbsolute(self.xpsAxes[1], posZ_abs)
                    self.clear_error_message()
                self.updatePosition()
                
            elif btn == "ForwardTogether":
                x_ok = limit_min_x <= (posX_current + posX_rel) <= limit_max_x
                z_ok = limit_min_z <= (posZ_current + posZ_rel) <= limit_max_z
                if not x_ok or not z_ok:
                    error_msg = "Together forward step failed: One or both new positions would exceed travel limits"
                    self.display_error_message(error_msg, "ERROR")
                else:
                    self.xps.moveRelative(self.xpsAxes[0], posX_rel)
                    self.xps.moveRelative(self.xpsAxes[1], posZ_rel)
                    self.clear_error_message()
                self.updatePosition()
                
            elif btn == "BackwardTogether":
                x_ok = limit_min_x <= (posX_current - posX_rel) <= limit_max_x
                z_ok = limit_min_z <= (posZ_current - posZ_rel) <= limit_max_z
                if not x_ok or not z_ok:
                    error_msg = "Together backward step failed: One or both new positions would exceed travel limits"
                    self.display_error_message(error_msg, "ERROR")
                else:
                    self.xps.moveRelative(self.xpsAxes[0], -1*posX_rel)
                    self.xps.moveRelative(self.xpsAxes[1], -1*posZ_rel)
                    self.clear_error_message()
                self.updatePosition()
        elif btn in ("AbsoluteTogether", "ForwardTogether", "BackwardTogether"):
            error_msg = f"Together mode failed: Both stages must be in ready state. Current status - X: {self.xpsStageStatus[0]}, Z: {self.xpsStageStatus[1]}"
            self.display_error_message(error_msg, "ERROR")

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
                self.ui.z_abs_mv_bt.setEnabled(False)
                self.ui.z_step_f_bt.setEnabled(False)
                self.ui.z_step_b_bt.setEnabled(False)
                self.ui.abs_mv_together_bt.setEnabled(False)
                self.ui.step_fwd_together_bt.setEnabled(False)
                self.ui.step_bckwd_together_bt.setEnabled(False)
                self.ui.x_status.setText("Not Initialized")
                self.ui.z_status.setText("Not Initialized")
                
            elif self.xpsStageStatus[0] == "Not referenced state":
                self.ui.home_xps_bt.setEnabled(True)
                self.ui.enable_dis_xps_bt.setEnabled(False)
                self.ui.x_abs_mv_bt.setEnabled(False)
                self.ui.x_step_f_bt.setEnabled(False)
                self.ui.x_step_b_bt.setEnabled(False)
                self.ui.z_abs_mv_bt.setEnabled(False)
                self.ui.z_step_f_bt.setEnabled(False)
                self.ui.z_step_b_bt.setEnabled(False)
                self.ui.abs_mv_together_bt.setEnabled(False)
                self.ui.step_fwd_together_bt.setEnabled(False)
                self.ui.step_bckwd_together_bt.setEnabled(False)
                self.ui.x_status.setText("Not Homed")
                self.ui.z_status.setText("Not Homed")
                
            elif self.xpsStageStatus[0] == "Disabled state":
                self.ui.enable_dis_xps_bt.setEnabled(True)
                self.ui.init_xps_bt.setEnabled(False)
                self.ui.home_xps_bt.setEnabled(False)
                self.ui.x_abs_mv_bt.setEnabled(False)
                self.ui.x_step_f_bt.setEnabled(False)
                self.ui.x_step_b_bt.setEnabled(False)
                self.ui.z_abs_mv_bt.setEnabled(False)
                self.ui.z_step_f_bt.setEnabled(False)
                self.ui.z_step_b_bt.setEnabled(False)
                self.ui.abs_mv_together_bt.setEnabled(False)
                self.ui.step_fwd_together_bt.setEnabled(False)
                self.ui.step_bckwd_together_bt.setEnabled(False)
                self.ui.x_status.setText("Disabled")
                self.ui.z_status.setText("Disabled")
                
            elif self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                self.ui.enable_dis_xps_bt.setEnabled(True)
                self.ui.init_xps_bt.setEnabled(False)
                self.ui.home_xps_bt.setEnabled(False)
                self.ui.x_status.setText("Enabled")
                self.ui.z_status.setText("Enabled")
                # Delegate motion button enable/disable to the movement mode handler
                self.updateMovementMode()
                   
        self.updatePosition()
    
    
    def updatePosition(self):
        if self.xps:
            self.ui.x_pos_disp.setText(str(self.xps.getStagePosition(self.xpsAxes[0])))         
            self.ui.z_pos_disp.setText(str(self.xps.getStagePosition(self.xpsAxes[1])))
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
            
        elif lim == "minXPSZ":
            try:
                limit = float(self.ui.z_min_trav_ip.text())
                if limit < 0 or limit > 50:
                    error_msg = f"Z-axis minimum limit invalid: {limit:.2f} mm is outside allowed range [0, 50] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_z.setText('Invalid minimum limit')
                    self.ui.z_min_trav_ip.setText(str(self.xps.getminLimit(self.xpsAxes[1])))
                else:
                    self.xps.setminLimit(self.xpsAxes[1],limit)
                    self.clear_error_message()
            except:
                pass
            
        elif lim == "maxXPSZ":
            try:
                limit = float(self.ui.z_max_trav_ip.text())
                if limit < 0 or limit > 50:
                    error_msg = f"Z-axis maximum limit invalid: {limit:.2f} mm is outside allowed range [0, 50] mm"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label_z.setText('Invalid maximum limit')
                    self.ui.z_max_trav_ip.setText(str(self.xps.getmaxLimit(self.xpsAxes[1])))
                else:
                    self.xps.setmaxLimit(self.xpsAxes[1],limit)
                    self.clear_error_message()
            except:
                pass
            
    
    def _initSavedPositions(self):
        """Create saved positions files with defaults if they don't exist."""
        default = {"x_pos": 0.1, "z_pos": 0.1}
        for filepath in self.saved_positions_files.values():
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump(default, f, indent=2)
    
    def savePosition(self, experiment):
        """Save the current stage positions to the experiment's JSON file."""
        if self.xps:
            try:
                x_pos = float(self.xps.getStagePosition(self.xpsAxes[0]))
                z_pos = float(self.xps.getStagePosition(self.xpsAxes[1]))
                positions = {"x_pos": x_pos, "z_pos": z_pos}
                with open(self.saved_positions_files[experiment], 'w') as f:
                    json.dump(positions, f, indent=2)
                info_msg = f"Saved {experiment} positions: X={x_pos} mm, Z={z_pos} mm"
                self.display_error_message(info_msg, "INFO")
            except Exception as e:
                error_msg = f"Error saving {experiment} positions: {e}"
                self.display_error_message(error_msg, "ERROR")
    
    def recallPosition(self, experiment):
        """Recall saved positions and move stages to those positions."""
        if self.xps:
            try:
                with open(self.saved_positions_files[experiment], 'r') as f:
                    positions = json.load(f)
                x_pos = positions["x_pos"]
                z_pos = positions["z_pos"]
                
                # Update the absolute move inputs to show where we're going
                self.ui.x_abs_mv_ip.setText(str(x_pos))
                self.ui.z_abs_mv_ip.setText(str(z_pos))
                
                # Move both stages to saved positions
                if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                    self.xps.moveAbsolute(self.xpsAxes[0], x_pos)
                if self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
                    self.xps.moveAbsolute(self.xpsAxes[1], z_pos)
                
                self.updatePosition()
                info_msg = f"Recalled {experiment} positions: X={x_pos} mm, Z={z_pos} mm"
                self.display_error_message(info_msg, "INFO")
            except FileNotFoundError:
                error_msg = f"No saved {experiment} positions file found"
                self.display_error_message(error_msg, "ERROR")
            except Exception as e:
                error_msg = f"Error recalling {experiment} positions: {e}"
                self.display_error_message(error_msg, "ERROR")
        
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
            self.display_camera_image(image, self.ui.LiveFeedLabel)
    
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
    
    def save_captured_image_btn(self):
        """Save the last captured image with a filename based on image counter and EF delay."""
        if self.last_saved_image is None:
            self.cam_log("No captured image to save.")
            return
        save_dir = os.path.join(script_dir, "FLIR Camera Images")
        os.makedirs(save_dir, exist_ok=True)
        delay_val = str(self.dg_values["E"][1])
        delay_unit = str(self.dg_values["E"][2])
        delay_str = delay_val.replace(".", "-")
        filename = f"test_{self.image_counter}_chE_{delay_str}_{delay_unit}.bmp"
        filepath = os.path.join(save_dir, filename)
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
    
    def setDelaysDG(self):
        self.shot_mode = self.ui.shot_mode_select.currentText()
        
        #Setting the offset and amplitude vaslues 
        # Rotation stage - channel AB
        #Sets the offset value and amplitude value
        offset_val = 0
        self.dg_values['AB'][0] = offset_val
        amp_val = 3 
        self.dg_values['AB'][1] = amp_val
        self.ins_dg.get_voltage('AB', offset_val, amp_val)
        self.ins_dg.set_voltage()
        #Then displays the change on the delay generator    
        self.ins_dg.display_amplitdue('AB')
        
        # Laser IP - channel CD
        #Sets the offset value and amplitude value
        offset_val = 0
        self.dg_values['CD'][0] = offset_val
        amp_val = 1.5 
        self.dg_values['CD'][1] = amp_val
        self.ins_dg.get_voltage('CD', offset_val, amp_val)
        self.ins_dg.set_voltage()
        #Then displays the change on the delay generator    
        self.ins_dg.display_amplitdue('CD')
        
        # Camera trigger - channel EF
        #Sets the offset value and amplitude value
        offset_val = 0
        self.dg_values['EF'][0] = offset_val
        amp_val = 2.8 
        self.dg_values['EF'][1] = amp_val
        self.ins_dg.get_voltage('EF', offset_val, amp_val)
        self.ins_dg.set_voltage()
        #Then displays the change on the delay generator    
        self.ins_dg.display_amplitdue('EF')
        
        if self.shot_mode == 'Single Rotation':
            #Calculates the delay for the delay generator
            self.dg_delay = ((self.step_per_rev)/self.freq)
            self.dg_delay_rot = round((self.dg_delay + self.ref_delay),6)
            self.dg_delay_laser = round((self.dg_delay),6)
            
            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('B', 'A')
            
            # Setting the delay for the rotation stage - channel AB
            self.dg_values['B'][1] = self.dg_delay_rot
            self.dg_values['B'][2] = 's'
            self.ins_dg.get_delay('B', 'A', self.dg_delay_rot, 's')
            self.ins_dg.set_delay()
            
            
            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('D', 'C')
            
            # Setting the delay for the laser - channel CD
            self.dg_values['D'][1] = self.dg_delay_laser
            self.dg_values['D'][2] = 's'
            self.ins_dg.get_delay('D', 'C', self.dg_delay_laser, 's')
            self.ins_dg.set_delay()
            
            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('C', 'A')
              
            self.dg_values['C'][1] = float(self.ref_delay_dg)
            self.dg_values['C'][2] = 'ms'
            self.ins_dg.get_delay('C', 'A', (float(self.ref_delay_dg)), 'ms')
            self.ins_dg.set_delay()
            
            # Camera trigger - channel E linked to A
            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('E', 'A')
              
            self.dg_values['E'][1] = float(self.ref_delay_dg)
            self.dg_values['E'][2] = 'ms'
            self.ins_dg.get_delay('E', 'A', (-1*float(self.ref_delay_dg)), 'ms')
            self.ins_dg.set_delay()
            
        else:
            self.dg_delay = ((self.step_num)/self.freq)
            self.dg_delay_rot = round((self.dg_delay + self.ref_delay),6)
            self.dg_delay_laser = round((self.dg_delay),6)

            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('B', 'A')
            
            # Setting the delay for the rotation stage - channel AB
            self.dg_values['B'][1] = self.dg_delay_rot
            self.dg_values['B'][2] = 's'
            self.ins_dg.get_delay('B', 'A', self.dg_delay_rot, 's')
            self.ins_dg.set_delay()
            
            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('D', 'C')

            # Setting the delay for the laser - channel CD
            self.dg_values['D'][1] = self.dg_delay_laser
            self.dg_values['D'][2] = 's'
            self.ins_dg.get_delay('D', 'C', self.dg_delay_laser, 's')
            self.ins_dg.set_delay()
            
            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('C', 'A')
              
            self.dg_values['C'][1] = float(self.ref_delay_dg)
            self.dg_values['C'][2] = 'ms'
            self.ins_dg.get_delay('C', 'A', float(self.ref_delay_dg), 'ms')
            self.ins_dg.set_delay()
            
            # Camera trigger - channel E linked to A
            #set the new channel link in case there was a change 
            self.ins_dg.change_delay_link('E', 'A')
              
            self.dg_values['E'][1] = float(self.ref_delay_dg)
            self.dg_values['E'][2] = 'ms'
            self.ins_dg.get_delay('E', 'A', float(self.ref_delay_dg), 'ms')
            self.ins_dg.set_delay()
            
    
    def StartRot(self):
        
        # Setting up for values the rotation stage needs
        self.delay_cmd = ''
        self.rot_delay_cmd = ''
        self.delay_cmd = 'DELAY+'+str(self.delay_value_rot)
        self.rot_delay_cmd = 'DELAYROT+'+str(self.ref_delay)
        self.start_command = 'START'
        
        # Assuming the sepration along the cylinders edge is the same as the shot
        # separation
        # converting it to mm
        self.cylinder_sep_mm = float(self.ui.shot_sep_ip.text())*1e-3
        self.ui.x_step_ip.setText(str(self.cylinder_sep_mm))
        
        if (self.shot_mode == 'Single Rotation') and (self.rpm != ''):
            # Recalculate RPM in case rep rate or other parameters changed
            self.CalculateRPM()
            # Set up the delay generator with current values
            self.setDelaysDG()
            if self.ui.single_rot_fw_ck.isChecked():
                try:
                    #Setting up the needed values for the rotation stage
                    self.s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    self.s.sendall(self.rot_delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.delay_cmd.encode())
                    sleep(0.2)
                    #Firing the delay generator then starting the rotation 
                    self.s.sendall(self.start_command.encode())
                    self.FireIns()
                                        
                    # Checking for a signal back 
                    self.done_sig = self.s.recv(1024).decode().strip()
                    
                    if self.done_sig == 'DONE':
                        #Updating the shots taken only after confirmation
                        self.num_shot_taken = self.num_shot_taken + self.shot_per_rot
                        self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
                        
                        info_msg = f"Single rotation (forward) completed successfully. {self.shot_per_rot} shots taken. Moving stage forward by {self.cylinder_sep_mm:.2f} mm."
                        self.display_error_message(info_msg, "INFO")
                        self.ui.status_label.setText('Finished the Rotation')
                        # Now stepping the stage forward
                        self.xpsMotionBtn("ForwardX")
                        self.ui.status_label.setText('Rotation Complete and Stage Moved, Ready for Next Fire')
                    elif self.done_sig == 'FAIL':
                        error_msg = "Single rotation (forward) failed: Trigger signal not detected within timeout. Check delay generator trigger and connections."
                        self.display_error_message(error_msg, "ERROR")
                        self.ui.status_label.setText('Trigger not detected')
                    else:
                        error_msg = f"Single rotation (forward) failed: Unexpected response from RPi: '{self.done_sig}'"
                        self.display_error_message(error_msg, "ERROR")
                        self.ui.status_label.setText('Unexpected RPi response')
                        
                    
                except ConnectionRefusedError:
                    error_msg = f"Raspberry Pi connection failed: Unable to connect to RPi at {HOST}:{PORT}. Check network connection and ensure RPi server is running."
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label.setText('RPi connection failed')
                except Exception as e:
                    error_msg = f"Single rotation (forward) failed: {str(e)}"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label.setText('Rotation error')
            elif self.ui.single_rot_bw_ck.isChecked():
                try:
                    self.s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    self.s.sendall(self.rot_delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.delay_cmd.encode())
                    sleep(0.2)
                    #Firing the delay generator then starting the rotation 
                    self.s.sendall(self.start_command.encode())
                    self.FireIns()
                    
                    # Checking for a signal back 
                    self.done_sig = self.s.recv(1024).decode().strip()
                    
                    if self.done_sig == 'DONE':
                        #Updating the shots taken only after confirmation
                        self.num_shot_taken = self.num_shot_taken + self.shot_per_rot
                        self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
                        
                        info_msg = f"Single rotation (backward) completed successfully. {self.shot_per_rot} shots taken. Moving stage backward by {self.cylinder_sep_mm:.2f} mm."
                        self.display_error_message(info_msg, "INFO")
                        self.ui.status_label.setText('Finished the Rotation')
                        # Now stepping the stage backwards
                        self.xpsMotionBtn("BackwardX")
                        self.ui.status_label.setText('Rotation Complete and Stage Moved, Ready for Next Fire')
                    elif self.done_sig == 'FAIL':
                        error_msg = "Single rotation (backward) failed: Trigger signal not detected within timeout. Check delay generator trigger and connections."
                        self.display_error_message(error_msg, "ERROR")
                        self.ui.status_label.setText('Trigger not detected')
                    else:
                        error_msg = f"Single rotation (backward) failed: Unexpected response from RPi: '{self.done_sig}'"
                        self.display_error_message(error_msg, "ERROR")
                        self.ui.status_label.setText('Unexpected RPi response')
                    
                    
                except ConnectionRefusedError:
                    error_msg = f"Raspberry Pi connection failed: Unable to connect to RPi at {HOST}:{PORT}. Check network connection and ensure RPi server is running."
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label.setText('RPi connection failed')
                except Exception as e:
                    error_msg = f"Single rotation (backward) failed: {str(e)}"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label.setText('Rotation error')
            else: 
                error_msg = "Single rotation mode error: Must select either Forward or Backward direction checkbox before starting rotation."
                self.display_error_message(error_msg, "WARNING")
                self.ui.status_label.setText('Select rotation direction')
                 

        elif (self.shot_mode == 'N Shot') and (self.rpm != ''):
            # Recalculate RPM in case rep rate or other parameters changed
            self.CalculateRPM()
            
            # Update step calculations for the current shot number
            self.updateStep4Shot()
            
            # Set up the delay generator with current values
            self.setDelaysDG()
            
            # Turning it into an integer 
            self.step_num = int(np.ceil(self.step_num))
            # Setting up the command
            self.shot_num_cmd = 'SHOTNO+'+str(self.step_num)
            if (self.step_num + self.step_taken) <= self.step_per_rev:
                try:
                    self.s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    self.s.sendall(self.rot_delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.shot_num_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.delay_cmd.encode())
                    sleep(0.2)
                    # Firing the delay generator then starting the rotation 
                    self.s.sendall(self.start_command.encode())
                    self.FireIns()
                    
                    # Checking for a signal back 
                    self.done_sig = self.s.recv(1024).decode().strip()
                    
                    if self.done_sig == 'DONE':
                        info_msg = f"N-shot mode completed successfully. {self.shot_num} shots taken ({self.step_num} steps). Total shots taken: {self.num_shot_taken + int(self.shot_per_step*self.step_num)}/{self.shot_per_rot}"
                        self.display_error_message(info_msg, "INFO")
                        self.ui.status_label.setText('Finished taking the Shots')
                    elif self.done_sig == 'FAIL':
                        error_msg = "N-shot mode failed: Trigger signal not detected within timeout. Check delay generator trigger and connections."
                        self.display_error_message(error_msg, "ERROR")
                        self.ui.status_label.setText('Trigger not detected')
                    else:
                        error_msg = f"N-shot mode failed: Unexpected response from RPi: '{self.done_sig}'"
                        self.display_error_message(error_msg, "ERROR")
                        self.ui.status_label.setText('Unexpected RPi response')
                     
                    
                except ConnectionRefusedError:
                    error_msg = f"Raspberry Pi connection failed: Unable to connect to RPi at {HOST}:{PORT}. Check network connection and ensure RPi server is running."
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label.setText('RPi connection failed')
                except Exception as e:
                    error_msg = f"N-shot mode failed: {str(e)}"
                    self.display_error_message(error_msg, "ERROR")
                    self.ui.status_label.setText('N-shot error')
                
                # Updating the status appropriately on the gui
                self.updateShotNo()

            else:
                self.step_avail2take = self.step_per_rev - (self.step_taken)
                self.shot_avail2take = int((self.step_avail2take/self.step_per_rev)*self.shot_per_rot)
                error_msg = f"N-shot mode error: Requested {self.shot_num} shots ({self.step_num} steps) exceeds available capacity. Shots available: {self.shot_avail2take}, Steps available: {self.step_avail2take}, Steps taken: {self.step_taken}/{self.step_per_rev}"
                self.display_error_message(error_msg, "ERROR")
                self.ui.status_label.setText(f"Only {self.shot_avail2take} shots left")
                
        else:
            # Handle case where RPM is not calculated
            if self.rpm == '':
                error_msg = "Rotation start failed: RPM not calculated. Please click 'Calculate RPM' button first to set motor speed based on target diameter and shot separation."
                self.display_error_message(error_msg, "ERROR")
                self.ui.status_label.setText('Calculate RPM first')
            else:
                error_msg = f"Rotation start failed: Unknown shot mode '{self.shot_mode}'. Please select either 'Single Rotation' or 'N Shot' mode."
                self.display_error_message(error_msg, "ERROR")
                self.ui.status_label.setText('Invalid shot mode')
        
    def DisconnectBtn(self):
        #Shutting down the XPS stages 
        if self.xps:
            if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[0])
            if self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[1])
            self.updateGUIStatus()
        
        #Shutdown for the Rpi
        discoonect_cmd = 'DISCONNECT'
        self.s.sendall(discoonect_cmd.encode())
        
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