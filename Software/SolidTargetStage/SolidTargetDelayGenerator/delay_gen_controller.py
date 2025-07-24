#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 16:21:51 2025

@author: christina strilets
"""

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import instruments as ik
import quantities as pq
import json
import time, sys
from time import sleep
import pyvisa
from delay_gen_gui import Ui_MainWindow

# When editing locally
#sys.path.insert(0,'/Users/christina/Documents/github/HusseinLab_UltrafastPlasmaScience/Hardware/Delay Generator DG645') 

# When it's on the lab computer
# sys.path.append('C:/Users/R2D2/Documents/CODE/Github/HusseinLab_UltrafastPlasmaScience/Hardware/Delay Generator DG645')
sys.path.append(r'C:\Users\C3PO\Documents\CODE\HusseinLab_UltrafastPlasmaScience\Hardware')
from DG645.dg645 import DelayGen

#%%
class delay_gen_app(QtWidgets.QMainWindow):
    def __init__(self):
        super(delay_gen_app,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    
        #Connecting the instrument
        self.ins_dg = DelayGen("COM4", 9600) # dg645
        
        # Reads in previous input for different channel levels 
        self.read_json()
        
        # Creating the user inputs / buttons for the gui 
        self.ui.delay_select.currentIndexChanged.connect(lambda: self.disp_ch("delay"))
        self.ui.voltage_select.currentIndexChanged.connect(lambda: self.disp_ch("voltage"))
         
        #Adjusting the delay values 
        self.ui.delay_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Val"))
        self.ui.unit_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Units"))
        
        #Adjusting the voltage values
        self.ui.offset_v.textChanged.connect(lambda: self.updateVoltvals("Offset_Val"))
        self.ui.amplitude_v.textChanged.connect(lambda: self.updateVoltvals("Amp_Val"))
        
        # #Buttons to fire and shutdown
        self.ui.stop_dg_bt.clicked.connect(self.DisconnectBtn)
        
        self.ui.start_dg_bt.clicked.connect(self.FireBtn)
        
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
        
        
    # Reads in the jason file
    def read_json(self):
        with open("Software\SolidTargetStage\SolidTargetDelayGenerator\delay_gen_gui_inputs.json", "r") as read_file:
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
            self.ui.channel_disp.setText(self.dg_values[channel][0])
            self.ui.delay_disp.setText(str(self.dg_values[channel][1]))   
            self.ui.unit_disp.setText(self.dg_values[channel][2])
            channel_select =  str(self.ui.delay_select.currentText())
            channel = str(self.ui.channel_disp.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.unit_disp.text())
            self.ins_dg.set_delay(channel_select, channel, delay, delay_units)
            
            
        elif widget == "voltage":
            channel = self.ui.voltage_select.currentText()
            self.ui.offset_v.setText(str(self.dg_values[channel][0]))
            self.ui.amplitude_v.setText(str(self.dg_values[channel][1]))
            voltage_select = str(self.ui.voltage_select.currentText())
            offset_v = float(self.ui.offset_v.text())
            amplitude_v = float(self.ui.amplitude_v.text())
            self.ins_dg.set_voltage(voltage_select, offset_v, amplitude_v)
    
    
    def updateDelayvals(self, widget):
        channel = self.ui.delay_select.currentText()
        self.ui.channel_disp.setText(self.dg_values[channel][0])      
        if widget == "Delay_Val" and (self.ui.delay_disp.text() != ''):
            delay = float(self.ui.delay_disp.text())
            self.dg_values[channel][1] = delay
        elif widget == "Delay_Units" and (self.ui.unit_disp.text() != ''):
            delay_units = str(self.ui.unit_disp.text())
            self.dg_values[channel][2] = delay_units
         
        if self.ui.channel_disp.text() != "" and self.ui.delay_disp.text() != "" and self.ui.unit_disp.text() != "":
            channel_select =  str(self.ui.delay_select.currentText())
            channel = str(self.ui.channel_disp.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.unit_disp.text())
            self.ins_dg.set_delay(channel_select, channel, delay, delay_units)
            
            
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
            self.ins_dg.set_voltage(voltage_select, offset_v, amplitude_v)
    

    

   
    def change_display_bt(self, btn):
        self.ins_dg.change_display(btn)
              
    def DisconnectBtn(self):
        # First writing the json file to save current settings
        with open("Software\SolidTargetStage\SolidTargetDelayGenerator\delay_gen_gui_inputs.json", "r+") as write_file:
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
        # Disconnecting the device now
        self.ins_dg.disconnect_dg()
    
    def FireBtn(self):
        self.ins_dg.single_shot_fire_dg()
    

       
  
            
            

       

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = delay_gen_app()
    application.show()
    sys.exit(app.exec_()) 