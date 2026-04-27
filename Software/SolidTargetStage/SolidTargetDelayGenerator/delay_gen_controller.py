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
from delay_gen_ui import Ui_MainWindow
import os

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
class delay_gen_app(QtWidgets.QMainWindow):
    def __init__(self):
        super(delay_gen_app,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    
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
        
        #Buttons to fire and shutdown
        self.ui.stop_dg_bt.clicked.connect(self.DisconnectBtn)
        
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
    
    
              
    def DisconnectBtn(self):
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
    

       

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = delay_gen_app()
    application.show()
    sys.exit(app.exec_()) 
# %%
