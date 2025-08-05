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

from Software.SolidTargetStage.prelim_solid_stage_gui import Ui_MainWindow


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
        self.ref_delay_units = 'ms'
        self.rpm = ''
        self.dg_delay = 0
        self.ui.single_rot_fw_ck.setEnabled(True)
        self.ui.single_rot_bw_ck.setEnabled(True)
        self.step_per_rev = 400
        
        #Connecting to Rpi
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))
        
        
        
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
        
                        
        #Adjusting and updating rotation stage diameter
        self.ui.target_diam_ip.textChanged.connect(self.updateDiameter)
        
        # Calculating the RPM button
        self.ui.rpm_bt.clicked.connect(self.CalculateRPM)
        
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
            
    
    def update_shot_no(self):   
        self.shot_num = str(self.ui.shot_no_ip.text())
        if  self.shot_num != '':
            self.shot_num = int(self.ui.shot_no_ip.text())
        
    def update_rot_stage_delay(self):
        self.ref_delay = float(self.ui.rel_delay_ip.text())*1e-3
    
    def updateDiameter(self):
        self.diam_target = str(self.ui.target_diam_ip.text())
    
    def RelDelayBtn(self):
        self.ref_delay = float(self.ui.rel_delay_ip.text())*1e-3
        
    def CalculateRPM(self):
        #Parameters needed to calculate the rpm
        self.sep = 100*1e-6
        self.diam_target = str(self.ui.target_diam_ip.text())
        rep_rate = float(self.ui.rep_rate_select.currentText()) 
        if (self.diam_target != ''): 
            self.radius =  float(self.diam_target)*0.5            
            self.rpm = (self.sep/(self.radius*1e-3))*(1/(2*np.pi))*60*1000*rep_rate
            
            # Calculating how many shots one can take in one rotation 
            self.shot_per_rot = int((2*np.pi*self.radius)/(self.sep))
            
            
            #Seeing if the rpm is too low
            freq = self.rpm*self.step_per_rev*(1/60)
            self.delay_value_rot = (1/freq)*0.5
            
            #Calculates the delay for the delay generator 
            self.dg_delay = ((self.step_per_rev)/freq)+(float(self.ref_delay)*1e-3)
            
            if (1e6*self.delay_value_rot) < 5:
                self.ui.status_label.setText("Motor cannot support this RPM")
                self.rpm = ''
            else:
                self.rpm = str(self.rpm)
                self.ui.shot_per_rot_disp.setText(str(self.shot_per_rot))
                if self.num_shot_taken == 0:
                    self.ui.shots_left_disp.setText(str(self.shot_per_rot))
                    
                
                
    def StartRot(self):

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
                    self.s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    self.s.sendall(self.rot_delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.start_command.encode())
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
                    self.s.sendall(self.start_command.encode())
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
            else: 
                self.ui.status_label.setText('Must Select a Forward or Backward Step')
                 

        elif (self.shot_mode == 'N Shot') and (self.rpm != ''):
            self.step_num = int((self.shot_num/ self.shot_per_rot)*self.step_per_rev)
            self.shot_num_cmd = 'SHOTNO+'+str(self.step_num)
            if (self.shot_num+ self.num_shot_taken) < self.shot_per_rot:
                try:
                    self.s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    self.s.sendall(self.rot_delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.shot_num_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.start_command.encode())
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
                
                #Updating the status appropriately on the gui
                self.num_shot_taken = self.num_shot_taken+self.shot_num
                self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
                self.shot_left = self.shot_per_rot - self.num_shot_taken
                self.ui.shots_left_disp.setText(str(self.shot_left))
            else:
                self.num_shot_taken = (self.shot_num+ self.num_shot_taken) - self.shot_per_rot
                self.shot_per_rot = self.shot_per_rot - self.num_shot_taken
                try:
                    self.s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    self.s.sendall(self.rot_delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.shot_num_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.delay_cmd.encode())
                    sleep(0.2)
                    self.s.sendall(self.start_command.encode())
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
                
                #Updating the status appropriately on the gui
                self.ui.shots_taken_disp.setText(str(self.num_shot_taken))
                self.ui.shots_left_disp.setText(str(self.shot_left))
                
                
                
                

        
        
        
        
        
    def DisconnectBtn(self):
        QtWidgets.QApplication.quit()
        
        #Shutdown for the Rpi
        discoonect_cmd = 'DISCONNECT'
        self.s.sendall(discoonect_cmd.encode())
        
           

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = solid_target_stage_app_stage_app()
    application.show()
    sys.exit(app.exec_()) 