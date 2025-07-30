#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 12:58:22 2025

@author: christina
"""

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import numpy as np
import time, sys
from time import sleep
from rotation_stage_GUI import Ui_MainWindow
import os
import socket


# Whats needed to connect to the RPi
HOST = '172.29.115.25'  # Replace with Raspberry Pi's IP
PORT = 65432

# # Makes sure you are in the right path!
# cwd = os.getcwd()
# if "HusseinLab_UltrafastPlasmaScience" not in cwd.split(os.path.sep):
#     raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")
# # Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience', prevent import errors
# cwd = os.path.sep.join(
#     cwd.split(os.path.sep)[: cwd.split(os.path.sep).index("HusseinLab_UltrafastPlasmaScience") + 1]
# )
# sys.path.insert(0, cwd)

#%%
class rotation_stage_app(QtWidgets.QMainWindow):
    def __init__(self):
        super(rotation_stage_app,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Defining important values
        self.shot_mode = self.ui.shot_mode_select.currentText()
        self.shot_num = str(self.ui.shot_no_ip.text())
        self.rep_rate = float(self.ui.rep_rate_select.currentText())
        self.rpm = ''
        
        
        # Selecting the rep rate 
        self.ui.rep_rate_select.currentIndexChanged.connect(self.select_rep_rate)
        
        # Selecting the shot mode
        self.ui.shot_mode_select.currentIndexChanged.connect(self.select_shot_mode)
        
        #Selecting the number of shots
        self.ui.shot_no_ip.textChanged.connect(self.update_shot_no)
                        
        #Adjusting and updating rotation stage diameter
        self.ui.target_diam_ip.textChanged.connect(self.updateDiameter)
        
        # Calculating the RPM button
        self.ui.rpm_bt.clicked.connect(self.CalculateRPM)
        
        # Setting the Start Button
        self.ui.start_rot_bt.clicked.connect(self.StartRot)
        
        #Setting the  disconnect
        self.ui.disconnect_rot_bt.clicked.connect(self.DisconnectBtn)
        

        
    def select_rep_rate(self):    
        self.rep_rate = float(self.ui.rep_rate_select.currentText())


    def select_shot_mode(self):    
        self.shot_mode = self.ui.shot_mode_select.currentText()
    
    def update_shot_no(self):   
        self.shot_num = str(self.ui.shot_no_ip.text())
        
    def updateDiameter(self):
        self.diam_target = str(self.ui.target_diam_ip.text())
        
    def CalculateRPM(self):
        #Parameters needed to calculate the rpm
        self.sep = 100*1e-6
        self.diam_target = str(self.ui.target_diam_ip.text())
        rep_rate = float(self.ui.rep_rate_select.currentText()) 
        if (self.diam_target != ''): 
            self.radius =  float(self.diam_target)*0.5            
            self.rpm = (self.sep/(self.radius*1e-3))*(1/(2*np.pi))*60*1000*rep_rate
            
            #Seeing if the rpm is too low
            step_per_rev = 400
            freq = self.rpm*step_per_rev*(1/60)
            self.delay = (1/freq)*0.5
            if (1e6*self.delay) < 5:
                self.ui.status_label.setText("Motor cannot support this RPM")
                self.rpm = ''
            else:
                self.rpm = str(self.rpm)
                self.ui.start_rot_bt.setEnabled(True)
                self.ui.disconnect_rot_bt.setEnabled(True)
                

    def StartRot(self):
        self.shot_mode = self.ui.shot_mode_select.currentText()
        self.delay = 'DELAY+'+str(self.delay)
        self.start_command = 'START'
        if (self.shot_mode == 'Single Rotation') and (self.rpm != ''):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((HOST, PORT))
                    s.sendall(self.shot_mode.encode())
                    sleep(0.2)
                    s.sendall(self.delay.encode())
                    sleep(0.2)
                    s.sendall(self.start_command.encode())
                    self.ui.status_label.setText(f'Shot Mode Set to:{self.shot_mode}')
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
        elif (self.shot_mode == 'N Shot') and (self.rpm != ''):
            self.shot_num = 'SHOTNO+'+str(self.ui.shot_no_ip.text())
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((HOST, PORT))
                    s.sendall(self.shot_mode.encode())
                    self.ui.status_label.setText(f'Shot Mode Set to:{self.shot_mode}')
                    sleep(0.2)
                    s.sendall(self.shot_num.encode())
                    self.ui.status_label.setText(f'No shots:{self.shot_num}')
                    sleep(0.2)
                    s.sendall(self.delay.encode())
                    sleep(0.2)
                    s.sendall(self.start_command.encode())
                except ConnectionRefusedError:
                    self.ui.status_label.setText('Failed to connect to Raspberry Pi.')
        
    def DisconnectBtn(self):
        QtWidgets.QApplication.quit()
           

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = rotation_stage_app()
    application.show()
    sys.exit(app.exec_()) 