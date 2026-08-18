#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 16:21:51 2025

@author: christina strilets
"""

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import instruments as ik
import json
import time, sys
from time import sleep
from linear_stage_delay_gen_combo_ui import Ui_Dialog
import os
from Hardware.XPS.XPS import XPS

# Add the script's own directory to sys.path so local modules (e.g. stage_controller_test_GUI) are found
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

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

from Hardware.DG645.dg645 import DelayGen

#%%
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        ######### DELAY GENERATOR SETUP #########
        
        #Connecting the instrument
        self.ins_dg = DelayGen("COM5", 9600) # dg645
        
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
        self.ui.delay_select_units.currentIndexChanged.connect(lambda: self.updateDelayvals("Delay_Units"))
        self.ui.channel_link.textChanged.connect(lambda: self.updateDelayvals("Channel_Link"))
        
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
        
        #Buttons to fire and disconnect delay generator
        self.ui.stop_dg_bt.clicked.connect(self.DisconnectDGBtn)
        
        self.ui.star_dg_bt.clicked.connect(self.FireBtn)
        
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
        
        ######### XPS STAGE SETUP #########
        
        self.xps = None
        self.xpsAxes = [None, None]
        
        # Defines the two xps controllers that are used
        #self.xpsAxes = [str(self.ui.x_stage_select.currentText()),str(self.ui.z_stage_select.currentText())]
        #print(self.xpsAxes)

        #GUI Interactions
        self.ui.x_min_trav_ip.setText('0')
        self.ui.x_max_trav_ip.setText('20')
        
        self.ui.z_min_trav_ip.setText('0')
        self.ui.z_max_trav_ip.setText('20')
        
        self.ui.x_abs_mv_ip.setText('0')
        self.ui.z_abs_mv_ip.setText('0')
        
        self.ui.x_step_ip.setText('0')
        self.ui.z_step_ip.setText('0')
        
        #XPS Commands
        
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
        
        #Stop Button (stops XPS stages)
        self.ui.stop_bt.clicked.connect(self.stopBtn)
        
    
    ######### DELAY GENERATOR FUNCTIONS #########
    
    #Reads in the json file
    def read_json(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "delay_gen_gui_inputs.json")
        with open(json_path, "r") as read_file:
            inputs = json.load(read_file)
            print(inputs)
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
            self.ui.delay_select_units.setCurrentText(self.dg_values[channel][2])
            
            channel_select =  str(self.ui.delay_select.currentText())
            channel = str(self.ui.channel_link.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.delay_select_units.currentText())
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
        if widget == "Channel_Link":
            # Save the user-edited channel link back into dg_values
            new_link = self.ui.channel_link.text()
            self.dg_values[channel][0] = new_link
        elif widget == "Delay_Val" and (self.ui.delay_disp.text() != ''):
            delay = float(self.ui.delay_disp.text())
            self.dg_values[channel][1] = delay
        elif widget == "Delay_Units" and (self.ui.delay_select_units.currentText() != ''):
            delay_units = str(self.ui.delay_select_units.currentText())
            self.dg_values[channel][2] = delay_units
         
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.delay_select_units.currentText() != "":
            channel_select =  str(self.ui.delay_select.currentText())
            channel_ref = str(self.ui.channel_link.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.delay_select_units.currentText())
            self.ins_dg.get_delay(channel_select, channel_ref, delay, delay_units)
            
            
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
    
    def trg_src_change(self):
        
        trg_src = str(self.ui.trigger_source_select.currentText())
        self.ins_dg.get_trg_src(trg_src)
    
    def SetTrigSrc(self):
        # Sets the value in case there was a change
        trg_src = str(self.ui.trigger_source_select.currentText())
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
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.delay_select_units.currentText() != "":
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
    
    
              
    def DisconnectDGBtn(self):
        # First writing the json file to save current settings
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "delay_gen_gui_inputs.json")
        with open(json_path, "r+") as write_file:
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
    
    
    def FireBtn(self):
        self.ins_dg.single_shot_fire_dg()


    ######### XPS STAGE FUNCTIONS #########
    
    # Function to update the x and y info 
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
                    print("Invalid travel input")                  
                else:
                    self.xps.moveAbsolute(self.xpsAxes[0],posX_abs)
                
                self.updatePosition()
            elif btn == "ForwardX":
                if (posX_rel+posX_current) < limit_min_x or (posX_current+posX_rel) > limit_max_x:
                    print("Invalid travel input")                  
                else:
                    self.xps.moveRelative(self.xpsAxes[0],posX_rel)
                self.updatePosition()
                
            elif btn == "BackwardX":
                if (posX_current-posX_rel) < limit_min_x or (posX_current-posX_rel) > limit_max_x:
                    print("Invalid travel input")                  
                else:
                    self.xps.moveRelative(self.xpsAxes[0],-1*posX_rel)
                self.updatePosition()
                
        if self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
            if btn == "AbsoluteZ" and self.ui.z_abs_mv_ck.isChecked():
                if posZ_abs < limit_min_z or posZ_abs > limit_max_z:
                    print("Invalid travel input")                  
                else:
                    self.xps.moveAbsolute(self.xpsAxes[1],posZ_abs)
                self.updatePosition()
            elif btn == "ForwardZ":
                if (posZ_current+posZ_rel) < limit_min_z or (posZ_current+posZ_rel) > limit_max_z:
                    print("Invalid travel input")                  
                else:
                    self.xps.moveRelative(self.xpsAxes[1],posZ_rel)
                self.updatePosition()
                
            elif btn == "BackwardZ":
                if (posZ_current-posZ_rel) < limit_min_z or (posZ_current-posZ_rel) > limit_max_z:
                    print("Invalid travel input")                  
                else:
                    self.xps.moveRelative(self.xpsAxes[1],-1*posZ_rel)
                self.updatePosition()

        # --- Together mode: move both axes simultaneously ---
        if self.xpsStageStatus[0][:11].upper() == "Ready state".upper() and self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
            if btn == "AbsoluteTogether" and self.ui.together_abs_mv_ck.isChecked():
                x_ok = limit_min_x <= posX_abs <= limit_max_x
                z_ok = limit_min_z <= posZ_abs <= limit_max_z
                if not x_ok or not z_ok:
                    print("Invalid travel input for together absolute move")
                else:
                    self.xps.moveAbsolute(self.xpsAxes[0], posX_abs)
                    self.xps.moveAbsolute(self.xpsAxes[1], posZ_abs)
                self.updatePosition()
                
            elif btn == "ForwardTogether":
                x_ok = limit_min_x <= (posX_current + posX_rel) <= limit_max_x
                z_ok = limit_min_z <= (posZ_current + posZ_rel) <= limit_max_z
                if not x_ok or not z_ok:
                    print("Invalid travel input for together forward step")
                else:
                    self.xps.moveRelative(self.xpsAxes[0], posX_rel)
                    self.xps.moveRelative(self.xpsAxes[1], posZ_rel)
                self.updatePosition()
                
            elif btn == "BackwardTogether":
                x_ok = limit_min_x <= (posX_current - posX_rel) <= limit_max_x
                z_ok = limit_min_z <= (posZ_current - posZ_rel) <= limit_max_z
                if not x_ok or not z_ok:
                    print("Invalid travel input for together backward step")
                else:
                    self.xps.moveRelative(self.xpsAxes[0], -1*posX_rel)
                    self.xps.moveRelative(self.xpsAxes[1], -1*posZ_rel)
                self.updatePosition()
        elif btn in ("AbsoluteTogether", "ForwardTogether", "BackwardTogether"):
            print("Both stages must be ready to move together")

        #GUI Interface
        self.updateGUIStatus()
    
    
    '''Combined Functions'''
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
                    print("Invalid minimum limit")
                    self.ui.x_min_trav_ip.setText(str(self.xps.getminLimit(self.xpsAxes[0])))
                else:
                    self.xps.setminLimit(self.xpsAxes[0],limit)
            except:
                pass
            
        elif lim == "maxXPSX":
            try:
                limit = float(self.ui.x_max_trav_ip.text())
                if limit < 0 or limit > 50:
                    
                    print("Invalid maximum limit")
                    self.ui.x_max_trav_ip.setText(str(self.xps.getmaxLimit(self.xpsAxes[0])))
                else:
                    self.xps.setmaxLimit(self.xpsAxes[0],limit)
            except:
                pass
            
        elif lim == "minXPSZ":
            try:
                limit = float(self.ui.z_min_trav_ip.text())
                if limit < 0 or limit > 50:
                    print("Invalid minimum limit")
                    self.ui.z_min_trav_ip.setText(str(self.xps.getminLimit(self.xpsAxes[1])))
                else:
                    self.xps.setminLimit(self.xpsAxes[1],limit)
            except:
                pass
            
        elif lim == "maxXPSZ":
            try:
                limit = float(self.ui.z_max_trav_ip.text())
                if limit < 0 or limit > 50:
                    
                    print("Invalid maximum limit")
                    self.ui.z_max_trav_ip.setText(str(self.xps.getmaxLimit(self.xpsAxes[1])))
                else:
                    self.xps.setmaxLimit(self.xpsAxes[1],limit)
            except:
                pass



    def stopBtn(self):
        if self.xps:
            if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[0])
            if self.xpsStageStatus[1][:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[1])
            self.updateGUIStatus()
            QtWidgets.QApplication.quit()
    
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
                print(f"Saved {experiment} positions: X={x_pos} mm, Z={z_pos} mm")
            except Exception as e:
                print(f"Error saving {experiment} positions: {e}")
    
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
                print(f"Recalled {experiment} positions: X={x_pos} mm, Z={z_pos} mm")
            except FileNotFoundError:
                print(f"No saved {experiment} positions file found")
            except Exception as e:
                print(f"Error recalling {experiment} positions: {e}")
            
            
        
   

       

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = MainWindow()
    application.show()
    sys.exit(app.exec_()) 
# %%
