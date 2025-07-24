#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 15:45:13 2025

@author: christina strilets
"""

import instruments as ik
import quantities as pq
import pyvisa

class DelayGen:
    '''
    
    Attributes
    ----------
   
    '''
    
    
    def __init__(self,com_port = "COM3", baud_rate = 9600):  
        # connects to the delay gen
        try:
            self.ins = ik.srs.SRSDG645.open_serial(port =com_port, baud = baud_rate)
        except:
            print("DG645 connection cannot be established.")

    
    def set_delay(self, channel_select,channel,delay,delay_units):
        # sets the delay for the chanel on the delay gen
        
        print(self.ins.channel[channel_select].delay)
        print(self.ins.channel[channel], pq.Quantity(delay, delay_units))
        #try:
        #self.ins.channel[channel_select].delay = (self.ins.channel[channel], pq.Quantity(delay, delay_units))
            #ins.channel["A"].delay = (ins.channel[self.A_ch.toPlainText()], pq.Quantity(float(self.A_delay.toPlainText()), self.A_delay_unit.toPlainText()))
        #except:
        #    print("ERROR: check channel delay inputs")
        
               
    
    def set_voltage(self, voltage_select, offset_v, amplitude_v):
        # Sets the offset on the delay gen
        try:
            self.ins.output[voltage_select].level_offset = pq.Quantity(float(offset_v), "V")
            self.ins.output[voltage_select].level_amplitude = pq.Quantity(float(amplitude_v), "V")
        except:
            print("ERROR: check channel voltage inputs")


    
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

    
    def disconnect_dg(self):        
        # Disconnects the device
        self.ins.sendcmd("IFRS 0")
        
    def single_shot_fire_dg(self):
        # sends a single shot 
        self.ins.sendcmd('TSRC 5')
        self.ins.sendcmd('*TRG')



     

            


