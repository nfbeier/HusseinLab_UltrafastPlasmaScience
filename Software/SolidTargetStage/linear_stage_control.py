#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 09:31:21 2025

@author: christina
"""
import time, sys
import numpy as np
from scipy import constants
from PyQt5 import QtCore, QtGui, QtWidgets

# When editing locally
#sys.path.insert(0,'/Users/christina/Desktop/Hard X-ray Exp/Hardware/') #change to local computer git

# When working on lab computer
sys.path.append('C:/Users/R2D2/Documents/CODE/Github/HusseinLab_UltrafastPlasmaScience/Hardware')
# sys.path.append('C:/Users/nfbei/Documents/Research/Code/Github/HusseinLab_UltrafastPlasmaScience/Hardware')

from stage_controller_test_GUI import Ui_Dialog
from XPS.XPS import XPS



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
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
        
        #Stop Button
        self.ui.stop_bt.clicked.connect(self.stopBtn)
        
        
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
            
            #Selecting the different stages
            self.ui.x_stage_select.currentIndexChanged.connect(lambda: self.updateGroup(0))
            self.ui.z_stage_select.currentIndexChanged.connect(lambda: self.updateGroup(1))
            
        except AttributeError:
            self.xps = None
        #GUI Interface
        self.updateGUIStatus()
            
    # Function to update the x and y info 
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

        else:
            print("Stage not ready to move")
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
            
            
        
       

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = MainWindow()
    application.show()
    sys.exit(app.exec_()) 