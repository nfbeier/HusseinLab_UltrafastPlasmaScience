#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 15:45:13 2025

@author: christina strilets
"""

import instruments as ik
class DelayGen:
    '''
    
    Attributes
    ----------
   
    '''
    
    
    def __init__(self,com_port = "COM3", baud_rate = 9600):  
        # connects to the delay gen
        try:
            self.ins = ik.srs.SRSDG645.open_serial(port =com_port, baud = baud_rate)
        except Exception as e:
            print(f"An error occurred: {e}")
            print("DG645 connection cannot be established.")
            
            
    def get_delay(self, channel,channel_ref,delay,delay_units):
        delay_unit_dict = {
            "s" : "e0",
            "ms" : "e-3",
            "us" : "e-6",
            "ns" : "e-9",
            "ps" : "e-12",
            }
        
        ch_val = {
            "T0" : "1",
            "A" : "2",
            "B" : "3",
            "C" : "4",
            "D" : "5",
            "E" : "6",
            "F" : "7",
            "G" : "8",
            "H" : "9"
            }
        
        # Selects the appropriate channels for the delay
        channel = ch_val[channel]
        channel_ref = ch_val[channel_ref]
        
        # Sets up the delay values in a string format the instrument can read
        delay_unit_val = delay_unit_dict[delay_units]
        delay_val = str(delay)+delay_unit_val
        
        # Writes the delay command
        self.delay_cmd = "DLAY "+channel+","+channel_ref+","+delay_val

    
    def set_delay(self):
  
        try:
            self.ins.sendcmd(self.delay_cmd)
            
        except Exception as e:
           print(f"An error occurred: {e}")
    
    def get_voltage(self, voltage_select, offset_v, amplitude_v):
        # Sets the offset on the delay gen
        ch_val = {
            "AB" : "1",
            "CD" : "2",
            "EF" : "3",
            "GH" : "4",
            }
        #Selects the appropriate channel to set the voltage level
        voltage_select = ch_val[voltage_select]
        
        # Sets up the command lines for the generator to set the amplitude 
        # and offset 
        self.amplitude_cmd = "LAMP "+voltage_select+","+str(amplitude_v)
        self.offset_cmd = "LOFF "+voltage_select+","+str(offset_v)
        
        
               
    
    def set_voltage(self):
        # Sets the offset on the delay gen
        try:
            self.ins.sendcmd(self.amplitude_cmd)
            self.ins.sendcmd(self.offset_cmd)
        except Exception as e:
           print(f"An error occurred: {e}")


    def change_delay_link(self,ref,link):
        ch_val = {
            "T0" : "1",
            "A" : "2",
            "B" : "3",
            "C" : "4",
            "D" : "5",
            "E" : "6",
            "F" : "7",
            "G" : "8",
            "H" : "9"
            }
        # Selects the apporpriate channels
        ref_channel = ch_val[ref]
        link_channel = ch_val[link]
        
        # Makes sure you aren't linling a channelt to itsself
        if ref_channel == link_channel:
            print("invalid connection")
        else: 
            cmd = "LINK "+str(ref_channel)+","+str(link_channel)
            self.ins.sendcmd(cmd)
            
        
        
        
    def change_display(self, btn):
        # Displays the selected channel
        cmd = {
            "T0" : "DISP 11,0",
            "T1" : "DISP 11,1",
            "A" : "DISP 11,2",
            "B" : "DISP 11,3",
            "C" : "DISP 11,4",
            "D" : "DISP 11,5",
            "E" : "DISP 11,6",
            "F" : "DISP 11,7",
            "G" : "DISP 11,8",
            "H" : "DISP 11,9"
            }
        self.ins.sendcmd(cmd[btn])
    
    
    def display_amplitdue(self, btn):
        # Displays the selected channel
        cmd = {
            "AB" : "DISP 12,3",
            "CD" : "DISP 12,5",
            "EF" : "DISP 12,7",
            "GH" : "DISP 12,9",
            }
        self.ins.sendcmd(cmd[btn])

    
    def disconnect_dg(self):        
        # Disconnects the device
        self.ins.sendcmd("IFRS 0")
        
    def single_shot_fire_dg(self):
        # sends a single shot 
        self.ins.sendcmd('TSRC 5')
        self.ins.sendcmd('*TRG')



     

            


