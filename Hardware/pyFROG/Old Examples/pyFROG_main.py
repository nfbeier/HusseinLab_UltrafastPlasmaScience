# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 15:37:38 2020

@author: Sorry
"""

import sys
sys.path.append(r"C:\Users\nfbei\Documents\Research\Code\LAB-DO-GIT-GUD-pyFROG\Hardware Interface")
sys.path.append(r"C:\Users\nfbei\Documents\Research\Code\LAB-DO-GIT-GUD-pyFROG\Software\pyFROG")

from PyQt5 import QtWidgets,QtGui, QtCore
from pyFROG_gui import Ui_MainWindow
#from Newport_XPS.HelperClasses.XPS import XPS
import pandas as pd
import time
import pyqtgraph as pg
import numpy as np


class flameTriggerThread(QtCore.QRunnable):
    def __init__(self, flame,  shotDict = None):
        super(flameTriggerThread,self).__init__()
        self.flame = flame
        self.shotDict = shotDict
        
        if self.flame.saveSpectra.isChecked():
            numShots = 1 #Always single shot mode
           
            self.flame.num_of_scans.setValue(numShots)
            
    def run(self):
        if self.flame.saveSpectra.isChecked():
            self.flame.saveSpectraFunc(self.shotDict)
            
class mywindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(mywindow,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        #GUI Interactions
        self.ui.in_scanlen.setText('0.01')
        self.ui.in_scanstepnumbers.setText('10')
        self.ui.in_scanstepsize.setText('0.01')
        self.updateScanParameters(param='scanLength')
        
        self.ui.in_scanlen.textChanged.connect(lambda: self.updateScanParameters(param='scanLength'))
        self.ui.in_scanstepnumbers.textChanged.connect(lambda: self.updateScanParameters(param='numberSteps'))
        self.ui.in_scanstepsize.textChanged.connect(lambda: self.updateScanParameters(param='stepSize'))
        
        #XPS Initialization
        self.threadpool = QtCore.QThreadPool()
        self.xpsAxes = [str(self.ui.in_groupname.currentText())]
        self.xps = None#XPS()
        self.xpsGroupNames = None#self.xps.getXPSStatus()
        self.ui.in_groupname.clear()
        #self.ui.in_groupname.addItems(list(self.xpsGroupNames.keys()))
        #self.xps.setGroup(self.xpsAxes[0])
        self.xpsStageStatus = ["Not initialized state"]#[self.xps.getStageStatus(axis) for axis in self.xpsAxes]

        self.updateGUIStatus()
        
        #XPS Commands

        self.ui.STOP.clicked.connect(self.stopBtn)
        self.ui.p_actsetlim.clicked.connect(self.updateXPSTravelLimits)
        self.ui.p_actinit.clicked.connect(lambda: self.xpsInitialize())
        self.ui.p_actenable.clicked.connect(lambda: self.xpsEnableDisable())
        self.ui.p_actsaveposition.clicked.connect(lambda: self.savePosition())
        self.ui.p_acthome.clicked.connect(lambda: self.xpsHome())

        self.ui.in_groupname.currentIndexChanged.connect(lambda: self.updateGroup(0))

        self.ui.p_actabsmove.clicked.connect(lambda: self.xpsMove('Absolute'))
        self.ui.p_actsmallback.clicked.connect(lambda: self.xpsMove('SmallBack'))
        self.ui.p_actsmallforward.clicked.connect(lambda: self.xpsMove('SmallForward'))
        self.ui.p_actlargeback.clicked.connect(lambda: self.xpsMove('LargeBack'))
        self.ui.p_actlargeforward.clicked.connect(lambda: self.xpsMove('LargeForward'))

        #Flame commands
        
        self.ui.p_loadspec.clicked.connect(lambda: self.getSpectrum())
        self.ui.p_aquirescan.clicked.connect(lambda: self.aquireTrace())

        #Timer
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.updatePosition)
        self.timer.start()
    # ~~~~~~~General GUI Functions~~~~~~~
    def stopBtn(self):
        
        if self.xps:
            if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[0])

        sys.exit(0)
    #~~~~~~~XPS Base Functions~~~~~~~
    def savePosition(self):
        if self.xps:
            self.ui.out_saveposition.setText('%0.6f'%(self.xps.getStagePosition(self.xpsAxes[0])))
            self.in_actstatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]

    def xpsMove(self, btn):
        if self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
            if btn == "Absolute":
                if self.ui.c_actenableabs.isChecked():
                    posX = float(self.ui.in_actabsmove.text())
    
                    self.xps.moveAbsolute(self.xpsAxes[0],posX)
                else:
                    print('Absolute Move is Disabled')
            elif btn == "SmallForward":
                posX = float(self.ui.in_actsmallrel.text())
                self.xps.moveRelative(self.xpsAxes[0],posX)
            elif btn == "SmallBack":
                posX = float(self.ui.in_actsmallrel.text())
                self.xps.moveRelative(self.xpsAxes[0],-1*posX)
            elif btn == "LargeForward":
                posX = float(self.ui.in_actlargerel.text())
                self.xps.moveRelative(self.xpsAxes[0],posX)
            elif btn == "LargeBack":
                posX = float(self.ui.in_actlargerel.text())
                self.xps.moveRelative(self.xpsAxes[0],-1*posX)
            else:
                print('Error: \'%s\' is an invalid entry')
        else:
            print("Stage not ready to move")
            
    def xpsHome(self):
        self.xps.homeStage(self.xpsAxes[0])            
        self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
        self.updateGUIStatus()
        
    def updatePosition(self):
        if self.xps:
            self.ui.out_actcurrentpos.setText('{self.xps.getStagePosition(self.xpsAxes[0]):.6f} mm')
            self.in_actstatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
    def updateGroup(self):
        self.xpsAxes[0] = str(self.ui.in_groupname.currentText())
        self.xps.setGroup(self.xpsAxes[0])
        self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
        self.updateGUIStatus()
        
    def xpsInitialize(self):
            self.xps.initializeStage(self.xpsAxes[0])
            self.xps.initializeStage(self.xpsAxes[1])
            self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
            self.updateGUIStatus()
   
    def xpsEnableDisable(self):
        if self.xpsStageStatus[0].upper() == "Disabled state".upper():
            self.xps.enableGroup(self.xpsAxes[0])
        elif self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
            self.xps.disableGroup(self.xpsAxes[0])
            
        self.xpsStageStatus = [self.xps.getStageStatus(axis) for axis in self.xpsAxes]
        self.updateGUIStatus()         
        
    def updateXPSTravelLimits(self):
        xpsMinLim = self.ui.in_actminlim
        xpsMaxLim = self.ui.in_actmaxlim
        print(xpsMinLim.text())
        print(xpsMaxLim.text())
        #main code
        time.sleep(.1)

        try:
            limit = float(xpsMinLim.text())
            if limit < 0 or limit > 50:
                print("Invalid minimum limit")
                xpsMinLim.setText(str(self.xps.getminLimit(self.xpsAxes[0])))
            else:
                self.xps.setminLimit(self.xpsAxes[0],limit)
        except:
            pass
            
        try:
            limit = float(xpsMaxLim.text())
            if limit < 0 or limit > 50:
                
                print("Invalid maximum limit")
                xpsMaxLim.setText(str(self.xps.getmaxLimit(self.xpsAxes[0])))
            else:
                self.xps.setmaxLimit(self.xpsAxes[0],limit)
        except:
            pass
        
        
    def updateGUIStatus(self):
        if self.xpsStageStatus[0] == "Not initialized state" or self.xpsStageStatus[0] == "Not initialized state due to a GroupKill or KillAll command":
            self.ui.p_actinit.setEnabled(True)
            self.ui.p_acthome.setEnabled(False)
            self.ui.p_actenable.setEnabled(False)
            self.ui.p_actabsmove.setEnabled(False)
            self.ui.p_actsmallback.setEnabled(False)
            self.ui.p_actsmallforward.setEnabled(False)
            self.ui.p_actlargeback.setEnabled(False)
            self.ui.p_actlargeforward.setEnabled(False)
            self.ui.in_actstatus.setText("Not Initialized")
        elif self.xpsStageStatus[0] == "Not referenced state":
            self.ui.p_actinit.setEnabled(False)
            self.ui.p_acthome.setEnabled(True)
            self.ui.p_actenable.setEnabled(False)
            self.ui.p_actabsmove.setEnabled(False)
            self.ui.p_actsmallback.setEnabled(False)
            self.ui.p_actsmallforward.setEnabled(False)
            self.ui.p_actlargeback.setEnabled(False)
            self.ui.p_actlargeforward.setEnabled(False)
            self.ui.in_actstatus.setText("Not Homed")
            
        elif self.xpsStageStatus[0] == "Disabled state":         
            self.ui.p_actinit.setEnabled(False)
            self.ui.p_acthome.setEnabled(False)
            self.ui.p_actenable.setEnabled(True)
            self.ui.p_actabsmove.setEnabled(False)
            self.ui.p_actsmallback.setEnabled(False)
            self.ui.p_actsmallforward.setEnabled(False)
            self.ui.p_actlargeback.setEnabled(False)
            self.ui.p_actlargeforward.setEnabled(False)
            self.ui.in_actstatus.setText("Disabled state")
            
        elif self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
            self.ui.p_actinit.setEnabled(False)            
            self.ui.p_acthome.setEnabled(False)
            self.ui.p_actenable.setEnabled(True)
            self.ui.p_actabsmove.setEnabled(True)
            self.ui.p_actsmallback.setEnabled(True)
            self.ui.p_actsmallforward.setEnabled(True)
            self.ui.p_actlargeback.setEnabled(True)
            self.ui.p_actlargeforward.setEnabled(True)
            self.ui.in_actstatus.setText("Ready state")

            
        self.updatePosition()
    #~~~~~~~Flame Base Functions~~~~~~~
    
    def getSpectrum(self):
        return self.ui.flameWidget.getSpectrum()


    
    #~~~~~~~Combined Functions~~~~~~~
    def aquireTrace(self,pause=0.005):
        
        data = self.getSpectrum()
        wavelength = data[0]
        num_steps = int(self.ui.in_scanstepnumbers.text())
        scanLength = float(self.ui.in_scanlen.text())
        step_size = float(self.ui.in_scanstepsize.text())
        
        delay = np.linspace(-0.5*scanLength,0.5*scanLength,num_steps)
        actsteps = 0.0*delay
        
        trace = np.zeros((num_steps,len(wavelength)))
        
        for ii in range(num_steps):
            trace[ii] = self.getSpectrum()[1]
            self.ui.plt_ac.clear()
            self.ui.plt_ac.plot(delay,np.sum(trace,axis=1))
            self.ui.plt_specac.clear()
            self.ui.plt_specac.plot(np.sum(trace,axis=0),wavelength)  
            self.ui.plt_trace.setImage(trace)
            time.sleep(pause)
            
    def updateScanParameters(self,param=None):

        
        if param == 'stepSize':
            if not(self.ui.in_scanstepnumbers.text()) == '' and not(self.ui.in_scanstepsize.text() == ''):
                self.ui.in_scanlen.setText(str(int(self.ui.in_scanstepnumbers.text())*float(self.ui.in_scanstepsize.text())))
        elif param == 'scanLength':
            if not(self.ui.in_scanlen.text()) == '' and not(self.ui.in_scanstepnumbers.text() == ''):
                self.ui.in_scanstepsize.setText(str(float(self.ui.in_scanlen.text())/int(self.ui.in_scanstepnumbers.text()))) 
        elif param == 'numberSteps':
            if not(self.ui.in_scanstepnumbers.text()) == '' and not(self.ui.in_scanstepsize.text() == ''):
                self.ui.in_scanlen.setText(str(int(self.ui.in_scanstepnumbers.text())*float(self.ui.in_scanstepsize.text()))) 

        else:
            print("Don't know how you triggered this but something went really wrong apparently in the updateScanparameters function")

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = mywindow()
    application.show()
    sys.exit(app.exec_())  