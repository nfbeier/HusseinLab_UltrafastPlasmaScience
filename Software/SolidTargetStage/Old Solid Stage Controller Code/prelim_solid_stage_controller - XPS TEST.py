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


# Makes sure you are in the right path!
cwd = os.getcwd()
if "HusseinLab_UltrafastPlasmaScience" not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")
# Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience', prevent import errors
cwd = os.path.sep.join(
    cwd.split(os.path.sep)[: cwd.split(os.path.sep).index("HusseinLab_UltrafastPlasmaScience") + 1]
)
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
        self.ui.x_max_trav_ip.setText('20')
        
        self.ui.z_min_trav_ip.setText('0')
        self.ui.z_max_trav_ip.setText('20')
        
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
        self.ui.rpm_bt.clicked.connect(self.CalculateRPM)
        
        
        
        ######## DELAY GENERATOR FUNCTIONS ##########
        # Reads in previous input for different channel levels 
        self.read_json()
        
        # Creating the user inputs / buttons for the gui 
        self.ui.delay_select.currentIndexChanged.connect(lambda: self.disp_ch("delay"))
        self.ui.voltage_select.currentIndexChanged.connect(lambda: self.disp_ch("voltage"))
         
        #Adjusting and updating the delay values 
        self.ui.delay_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Val"))
        self.ui.unit_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Units"))
        
        #Adjusting and updating the voltage values
        self.ui.offset_v.textChanged.connect(lambda: self.updateVoltvals("Offset_Val"))
        self.ui.amplitude_v.textChanged.connect(lambda: self.updateVoltvals("Amp_Val"))
        
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
        
        
        ####### COMBINED FUNCTIONS ########
        # Setting the Start Button
        self.ui.fire_dg_bt.clicked.connect(self.StartRot)
        
        #Setting the  disconnect
        self.ui.stop_bt.clicked.connect(self.DisconnectBtn)
        
        
        
        
    ######### ROTATION FUNCTIONS #########  
    
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
        self.shot_sep_prelim = str(self.ui.shot_sep_ip.text())
        if  self.shot_sep_prelim != '':
            self.shot_sep = float(self.ui.shot_sep_ip.text())*1e-6
    
    def update_shot_no(self):   
        self.shot_num = str(self.ui.shot_no_ip.text())
        if  self.shot_num != '':
            self.shot_num = int(self.ui.shot_no_ip.text())
            self.updateStep4Shot()
            
    def updateStep4Shot(self):
        # Parameters needed to calculate the step # given
        # the shot #
        self.step_num = 0
        self.step_num_text = ''
        self.sep = self.shot_sep
        self.diam_target = str(self.ui.target_diam_ip.text())
        rep_rate = float(self.ui.rep_rate_select.currentText()) 
        
        if self.shot_num == 1:
            self.step_num = 1
            self.ui.step_4_shot_disp.setText(str(self.step_num))
        elif self.diam_target!= '': 
            self.radius =  float(self.diam_target)*0.5            
            self.rpm = (self.sep/(self.radius*1e-3))*(1/(2*np.pi))*60*1000*rep_rate
            
            # Calculating how many shots one can take in one rotation 
            self.shot_per_rot = int((2*np.pi*self.radius*1e-3)/(self.sep))
            
            # Calculating the steps needed to take for given shot #
            self.step_num = ((self.shot_num/ self.shot_per_rot)*self.step_per_rev)
            
            # Displaying the results 
            self.step_num_text = f"{self.step_num:.2f}"
            self.ui.step_4_shot_disp.setText(self.step_num_text)
        
        #Calculates RPM again in case values were changed 
        self.CalculateRPM()
                   
        
    def update_rot_stage_delay(self):
        self.ref_delay_dg = str(self.ui.rel_delay_ip.text())
        if self.ref_delay_dg != '':
            self.ref_delay = float(self.ui.rel_delay_ip.text())*1e-3
            self.ref_delay_dg = str(self.ui.rel_delay_ip.text())
    
    def updateDiameter(self):
        self.diam_target = str(self.ui.target_diam_ip.text())
    
    def RelDelayBtn(self):
        self.ref_delay_dg = str(self.ui.rel_delay_ip.text())
        self.ref_delay = float(self.ui.rel_delay_ip.text())*1e-3
        
    def CalculateRPM(self):
        #Parameters needed to calculate the rpm
        self.sep = self.shot_sep
        self.diam_target = str(self.ui.target_diam_ip.text())
        rep_rate = float(self.ui.rep_rate_select.currentText()) 
        if (self.diam_target != ''): 
            self.radius =  float(self.diam_target)*0.5            
            self.rpm = (self.sep/(self.radius*1e-3))*(1/(2*np.pi))*60*1000*rep_rate
            
            # Calculating how many shots one can take in one rotation 
            self.shot_per_rot = int((2*np.pi*self.radius*1e-3)/(self.sep))
            
            #Calculating the nu,ber of steps taken in a single step
            self.shot_per_step = (1/self.step_per_rev)*((2*np.pi*self.radius*1e-3)/(self.sep))
            
            #Seeing if the rpm is too low
            self.freq = self.rpm*self.step_per_rev*(1/60)
            self.delay_value_rot = (1/self.freq)*0.5
            
            
            if (1e6*self.delay_value_rot) < 5:
                self.ui.status_label.setText("Motor cannot support this RPM")
                self.rpm = ''
            else:
                self.rpm = str(self.rpm)
            
            # sets up the delays on the delay generator 
            self.setDelaysDG()

        
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
            
        # else: 
        #     self.step_taken = (self.step_taken + self.step_num) - self.step_per_rev
        #     self.step_taken = int(self.step_taken)
        #     self.num_shot_taken = (self.num_shot_taken+ int(self.shot_per_step*self.step_num)) 

            
        #     #Updating the UI
        #     self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
        #     self.ui.progressBar.setValue(self.step_taken)
        #     self.ui.steps_taken_disp.setText(str(self.step_taken))
        
     
     ######### DELAY GEN FUNCTIONS ######### 
     
    #Reads in the json file
    def read_json(self):
        with open("delay_gen_gui_inputs.json", "r") as read_file:
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
        
    def disp_ch(self, widget):    
        if widget == "delay":
            channel = self.ui.delay_select.currentText()
            self.ui.channel_link.setText(self.dg_values[channel][0])
            self.ui.delay_disp.setText(str(self.dg_values[channel][1]))   
            self.ui.unit_disp.setText(self.dg_values[channel][2])
            
            channel_select =  str(self.ui.delay_select.currentText())
            channel = str(self.ui.channel_link.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.unit_disp.text())
            self.ins_dg.get_delay(channel_select, channel, delay, delay_units)
            
        elif widget == "voltage":
            channel = self.ui.voltage_select.currentText()
            self.ui.offset_v.setText(str(self.dg_values[channel][0]))
            self.ui.amplitude_v.setText(str(self.dg_values[channel][1]))
            
            voltage_select = str(self.ui.voltage_select.currentText())
            offset_v = float(self.ui.offset_v.text())
            amplitude_v = float(self.ui.amplitude_v.text())
            self.ins_dg.get_voltage(voltage_select, offset_v, amplitude_v)
    
     
    def updateDelayvals(self, widget):
        channel = self.ui.delay_select.currentText()
        self.ui.channel_link.setText(self.dg_values[channel][0])      
        if widget == "Delay_Val" and (self.ui.delay_disp.text() != ''):
            delay = float(self.ui.delay_disp.text())
            self.dg_values[channel][1] = delay
        elif widget == "Delay_Units" and (self.ui.unit_disp.text() != ''):
            delay_units = str(self.ui.unit_disp.text())
            self.dg_values[channel][2] = delay_units
         
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.unit_disp.text() != "":
            channel_select =  str(self.ui.delay_select.currentText())
            channel = str(self.ui.channel_link.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.unit_disp.text())
            self.ins_dg.get_delay(channel_select, channel, delay, delay_units)
            
            
    def updateVoltvals(self, widget):
        channel = self.ui.voltage_select.currentText()
        if widget == "Offset_Val" and (self.ui.offset_v.text() != ''):
            offset_val = float(self.ui.offset_v.text())
            self.dg_values[channel][0] = offset_val
        elif widget == "Amp_Val" and (self.ui.amplitude_v.text() != ''):
            amp_val = float(self.ui.amplitude_v.text())
            self.dg_values[channel][1] = amp_val
        
        if self.ui.offset_v.text() != "" and self.ui.amplitude_v.text() != "":
            voltage_select = str(self.ui.voltage_select.currentText())
            offset_v = float(self.ui.offset_v.text())
            amplitude_v = float(self.ui.amplitude_v.text())
            self.ins_dg.get_voltage(voltage_select, offset_v, amplitude_v)
    
   
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
                voltage_select = str(a)
                offset_v = float(self.dg_values[a][0])
                amplitude_v = float(self.dg_values[a][1])
                self.ins_dg.get_voltage(voltage_select, offset_v, amplitude_v)
                self.ins_dg.set_voltage()
            i = i+1


    def SetDelayBt(self):
        # Sets the value
        channel =  str(self.ui.delay_select.currentText())
        channel_ref = str(self.ui.channel_link.text())
        
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
        voltage_select = str(self.ui.voltage_select.currentText())
 
        sleep(0.2)
        if self.ui.offset_v.text() != "" and self.ui.amplitude_v.text() != "":
            self.ins_dg.set_voltage()
            #Then displays the change on the delay generator
            sleep(0.2)      
            self.ins_dg.display_amplitdue(voltage_select)
        
        
    # Fires Delay Generator / sends a single trigger    
    def FireIns(self):
        self.ins_dg.single_shot_fire_dg()
    
    
    ############## XPS STAGE  FUNCTIONS ##########################
    
    # Function initialize
    def _initXPS(self):
        #Initalizing the xps
        #Initialize XPS
        try:
            self.xps_ipaddress = str(self.ui.ip_address_ip.text())
            self.xps = XPS(self.xps_ipaddress)
            self.xpsGroupNames = self.xps.getXPSStatus()
            self.ui.x_stage_select.clear()
            self.ui.z_stage_select.clear()
            self.ui.x_stage_select.addItems(list(self.xpsGroupNames.keys()))
            self.ui.z_stage_select.addItems(list(self.xpsGroupNames.keys()))
            self.ui.z_stage_select.setCurrentIndex(1)
            self.xpsAxes = [str(self.ui.x_stage_select.currentText()),str(self.ui.z_stage_select.currentText())]
            
            self.xps.setGroup(self.xpsAxes[0])
            self.xps.setGroup(self.xpsAxes[1])
            self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
            
            self.ui.home_xps_bt.setEnabled(True)
            self.ui.enable_dis_xps_bt.setEnabled(True)
            self.ui.init_xps_bt.setEnabled(True)
            self.ui.stop_bt.setEnabled(True)
            
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
            self.xpsAxes[0] = str(self.ui.x_stage_select.currentText())
            self.xps.setGroup(self.xpsAxes[0])
        if axis == 1:
            self.xpsAxes[1] = str(self.ui.z_stage_select.currentText())
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
                    self.ui.status_label_x.setText('Invalid travel input')                  
                else:
                    self.xps.moveAbsolute(self.xpsAxes[0],posX_abs)
                    self.ui.status_label_x.setText('')
                self.updatePosition()
            elif btn == "ForwardX":
                if (posX_rel+posX_current) < limit_min_x or (posX_current+posX_rel) > limit_max_x:
                    self.ui.status_label_x.setText('Invalid travel input')                 
                else:
                    self.xps.moveRelative(self.xpsAxes[0],posX_rel)
                    self.ui.status_label_x.setText('')
                self.updatePosition()
                
            elif btn == "BackwardX":
                if (posX_current-posX_rel) < limit_min_x or (posX_current-posX_rel) > limit_max_x:
                    self.ui.status_label_x.setText('Invalid travel input')                  
                else:
                    self.xps.moveRelative(self.xpsAxes[0],-1*posX_rel)
                    self.ui.status_label_x.setText('')
                self.updatePosition()
                
        if self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
            if btn == "AbsoluteZ" and self.ui.z_abs_mv_ck.isChecked():
                if posZ_abs < limit_min_z or posZ_abs > limit_max_z:
                    self.ui.status_label_z.setText('Invalid travel input')                  
                else:
                    self.xps.moveAbsolute(self.xpsAxes[1],posZ_abs)
                    self.ui.status_label_z.setText('')
                self.updatePosition()
            elif btn == "ForwardZ":
                if (posZ_current+posZ_rel) < limit_min_z or (posZ_current+posZ_rel) > limit_max_z:
                    self.ui.status_label_z.setText('Invalid travel input')                   
                else:
                    self.xps.moveRelative(self.xpsAxes[1],posZ_rel)
                    self.ui.status_label_z.setText('')
                self.updatePosition()
                
            elif btn == "BackwardZ":
                if (posZ_current-posZ_rel) < limit_min_z or (posZ_current-posZ_rel) > limit_max_z:
                    self.ui.status_label_z.setText('Invalid travel input')                   
                else:
                    self.xps.moveRelative(self.xpsAxes[1],-1*posZ_rel)
                    self.ui.status_label_z.setText('')
                self.updatePosition()

        else:
            self.ui.status_label_z.setText('Stage not ready to move') 
            self.ui.status_label_x.setText('Stage not ready to move') 
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
                self.ui.x_status.setText("Disabled")
                self.ui.z_status.setText("Disabled")
                
            elif self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                self.ui.enable_dis_xps_bt.setEnabled(True)
                self.ui.init_xps_bt.setEnabled(False)
                self.ui.home_xps_bt.setEnabled(False)
                self.ui.x_abs_mv_bt.setEnabled(True)
                self.ui.x_step_f_bt.setEnabled(True)
                self.ui.x_step_b_bt.setEnabled(True)
                self.ui.z_abs_mv_bt.setEnabled(True)
                self.ui.z_step_f_bt.setEnabled(True)
                self.ui.z_step_b_bt.setEnabled(True)
                self.ui.x_status.setText("Enabled")
                self.ui.z_status.setText("Enabled")
                   
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
                    self.ui.status_label_x.setText('Invalid minimum limit')
                    self.ui.x_min_trav_ip.setText(str(self.xps.getminLimit(self.xpsAxes[0])))
                else:
                    self.xps.setminLimit(self.xpsAxes[0],limit)
            except:
                pass
            
        elif lim == "maxXPSX":
            try:
                limit = float(self.ui.x_max_trav_ip.text())
                if limit < 0 or limit > 50:
                    self.ui.status_label_x.setText('Invalid maximum limit')
                    self.ui.x_max_trav_ip.setText(str(self.xps.getmaxLimit(self.xpsAxes[0])))
                else:
                    self.xps.setmaxLimit(self.xpsAxes[0],limit)
            except:
                pass
            
        elif lim == "minXPSZ":
            try:
                limit = float(self.ui.z_min_trav_ip.text())
                if limit < 0 or limit > 50:
                    self.ui.status_label_z.setText('Invalid minimum limit')
                    self.ui.z_min_trav_ip.setText(str(self.xps.getminLimit(self.xpsAxes[1])))
                else:
                    self.xps.setminLimit(self.xpsAxes[1],limit)
            except:
                pass
            
        elif lim == "maxXPSZ":
            try:
                limit = float(self.ui.z_max_trav_ip.text())
                if limit < 0 or limit > 50:
                    self.ui.status_label_z.setText('Invalid maximum limit')
                    self.ui.z_max_trav_ip.setText(str(self.xps.getmaxLimit(self.xpsAxes[1])))
                else:
                    self.xps.setmaxLimit(self.xpsAxes[1],limit)
            except:
                pass
            
        
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
        
        self.ref_delay_dg = str(self.ui.rel_delay_ip.text())
        
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
            self.ins_dg.get_delay('C', 'A', float(self.ref_delay_dg), 'ms')
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
            
    
    def StartRot(self):       
        # Setting up for values the rotation stage needs
        self.delay_cmd = ''
        self.rot_delay_cmd = ''
        self.delay_cmd = 'DELAY+'+str(self.delay_value_rot)
        self.rot_delay_cmd = 'DELAYROT+'+str(self.ref_delay)
        self.start_command = 'START'
        
        # Assuming a 100 um steo along the cylinger's edge 
        self.single_step = str(0.1)
        self.ui.x_step_ip.setText(self.single_step)
        if (self.shot_mode == 'Single Rotation') and (self.rpm != ''):
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
                    
                    #Upating the shots taken 
                    self.num_shot_taken = self.num_shot_taken + self.shot_per_rot
                    self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
                    
                    if self.done_sig == 'DONE':
                        self.ui.status_label.setText('Finished the Rotation')
                        # Now stepping the stage forward
                        self.xpsMotionBtn("ForwardX")
                        self.ui.status_label.setText('Rotation Complete and Stage Moved, Ready for Next Fire')
                        
                    
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
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
                                        
                    #Upating the shots taken 
                    self.num_shot_taken = self.num_shot_taken + self.shot_per_rot
                    self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
                    
                    if self.done_sig == 'DONE':
                        self.ui.status_label.setText('Finished the Rotation')
                        # Now stepping the stage backwards
                        self.xpsMotionBtn("BackwardX")
                        self.ui.status_label.setText('Rotation Complete and Stage Moved, Ready for Next Fire')
                    
                    
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
            else: 
                self.ui.status_label.setText('Must Select a Forward or Backward Step')
                 

        elif (self.shot_mode == 'N Shot') and (self.rpm != ''):
            #Making sure we have the right shot #
            self.updateStep4Shot()
            #Turining it into an integer 
            self.step_num = int(np.ceil(self.step_num))
            # Setting up the command
            self.shot_num_cmd = 'SHOTNO+'+str(self.step_num)
            if (self.step_num+ self.step_taken) <= self.step_per_rev:
                try:
                    self.s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    self.s.sendall(self.rot_delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.shot_num_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.delay_cmd.encode())
                    sleep(0.2)
                    #Firing the delay generator then starting the rotation 
                    self.s.sendall(self.start_command.encode())
                    self.FireIns()
                    
                    # Checking for a signal back 
                    self.done_sig = self.s.recv(1024).decode().strip()
                    
                    if self.done_sig == 'DONE':
                        self.ui.status_label.setText('Finished taking the Shots')
                     
                    
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
                
                #Updating the status appropriately on the gui
                self.updateShotNo()

            else:
                try:
                    self.step_avail2take = self.step_per_rev - (self.step_taken)
                    self.shot_avail2take = int((self.step_avail2take/self.step_per_rev)*self.shot_per_rot)
                    self.ui.status_label.setText(f"Too many shots requested - Only have {self.shot_avail2take} shots left or {self.step_avail2take} steps left")
                   
                    
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
                
        
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
        with open("delay_gen_gui_inputs.json", "r+") as write_file:
            inputs = json.load(write_file)
            
            for i in ["A", "B", "C", "D", "E", "F", "G", "H"]:
                inputs[i+"_ch"] = self.dg_values[i][0]
                inputs[i+"_delay"] = self.dg_values[i][1]
                inputs[i+"_delay_unit"] = self.dg_values[i][2]
            for i in ["AB", "CD", "EF", "GH"]:
                inputs[i+"_offset"] = self.dg_values[i][0]
                inputs[i+"_Amp"] = self.dg_values[i][1]
                
            write_file.seek(0)
            json.dump(inputs, write_file)
            write_file.truncate()
            
        #Disconnecting the device now
        self.ins_dg.disconnect_dg()
        
        #Disconnecting the app now 
        QtWidgets.QApplication.quit()
        
           

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = solid_target_stage_app_stage_app()
    application.show()
    sys.exit(app.exec_()) 