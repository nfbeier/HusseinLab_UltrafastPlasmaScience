import pandas as pd
import time, sys
import pyqtgraph as pg
import numpy as np

from pyvisa import ResourceManager
from PyQt5 import QtCore, QtGui, QtWidgets
import qdarktheme
from instrumental import instrument, list_instruments
#from instrumental.drivers.spectrometers import thorlabs_ccs

sys.path.append('C:/Users/R2D2/Documents/CODE/Github/HusseinLab_UltrafastPlasmaScience/Hardware')
sys.path.append('C:/Users/nfbei/Documents/Research/Code/Github/HusseinLab_UltrafastPlasmaScience/Hardware')

from pyFROG_GUI import Ui_MainWindow
from XPS.XPS import XPS

class pyFROG_App(QtWidgets.QMainWindow):
    def __init__(self):
        super(pyFROG_App,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.threadpool = QtCore.QThreadPool()

        self.xps, self.spec = None, None

        #GUI Interactions
        self.ui.in_scanlen.setText('0.01')
        self.ui.in_scanstepnumbers.setText('10')
        self.ui.in_scanstepsize.setText('0.01')
        self.updateScanParameters(param='scanLength')
        
        self.ui.in_scanlen.textChanged.connect(lambda: self.updateScanParameters(param='scanLength'))
        self.ui.in_scanstepnumbers.textChanged.connect(lambda: self.updateScanParameters(param='numberSteps'))
        self.ui.in_scanstepsize.textChanged.connect(lambda: self.updateScanParameters(param='stepSize'))

        self.ui.ConnectXPS.clicked.connect(self._initXPS)
        self.ui.ConnectThorlabs.clicked.connect(self._initThorlabs)

        self.ui.actionExit.triggered.connect(self.stopBtn)
        self.ui.p_actsetlim.clicked.connect(self.updateXPSTravelLimits)
        self.ui.p_actinit.clicked.connect(lambda: self.xpsInitialize())
        self.ui.p_actenable.clicked.connect(lambda: self.xpsEnableDisable())
        self.ui.p_actsaveposition.clicked.connect(lambda: self.savePosition())
        self.ui.p_acthome.clicked.connect(lambda: self.xpsHome())

        self.ui.p_actabsmove.clicked.connect(lambda: self.xpsMove('Absolute'))
        self.ui.p_actsmallback.clicked.connect(lambda: self.xpsMove('SmallBack'))
        self.ui.p_actsmallforward.clicked.connect(lambda: self.xpsMove('SmallForward'))
        self.ui.p_actlargeback.clicked.connect(lambda: self.xpsMove('LargeBack'))
        self.ui.p_actlargeforward.clicked.connect(lambda: self.xpsMove('LargeForward'))

        #Timer
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.updatePosition)
        self.timer.start()

        #Load old data as reference
        file = r'Hardware\pyFROG\Old Examples\data\frg_trace_1580511001.pkl'
        data = pd.read_pickle(file)
        wave = data['wave'][0]
        trace = data['trace'][0].T
        self.ui.frogTracePlot.axTrace.imshow(trace,aspect = 'auto',extent = [-50,50,wave[0],wave[-1]],origin='lower')
        self.ui.frogTracePlot.ax_autoconv.plot(np.sum(trace,axis = 1),wave)
        self.ui.frogTracePlot.ax_autocorr.plot(np.sum(trace,axis = 0))
        self.ui.alignmentPlot.axes.plot(wave,trace[:,0])

    def _initXPS(self):
        self.xps = XPS(str(self.ui.in_actip.text()))
        self.xpsGroupNames = self.xps.getXPSStatus()
        self.ui.in_groupname.clear()
        self.ui.in_groupname.addItems(list(self.xpsGroupNames.keys()))
        self.xpsAxes = [str(self.ui.in_groupname.currentText())]
        self.xpsFROGAxis = self.xpsAxes[0]

        self.xps.setGroup(self.xpsFROGAxis)
        self.xpsStageStatus = self.xps.getStageStatus(self.xpsFROGAxis)
        self.updateGUIStatus()

    def _initThorlabs(self):
        #Spectrometer initialization
        rm = ResourceManager()
        res = rm.list_resources('?*::?*')
        
        if res:
            paramsets = list_instruments()
            self.spec = instrument(paramsets[0],reopen_policy = "reuse")# thorlabs ccs200
        
        self.wave = np.zeros((3648))
        self.intensity = np.zeros((3648)) 

        self.ui.alignmentPlot.axes.cla()
        self.ui.alignmentPlot.axes.plot(self.wave,self.intensity)
    
    def updateThorlabsParameters(self,param = None):
        if param == "integrationTime":
            self.spec.set_integration_time('{} ms')

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

    def xpsInitialize(self):
        self.xps.initializeStage(self.xpsFROGAxis)
        self.updateGUIStatus()

    def xpsHome(self):
        self.xps.homeStage(self.xpsFROGAxis)            
        self.updateGUIStatus()

    def xpsEnableDisable(self):
        self.xpsStageStatus = self.xps.getStageStatus(self.xpsFROGAxis)
        if self.xpsStageStatus.upper() == "Disabled state".upper():
            self.xps.enableGroup(self.xpsFROGAxis)
        elif self.xpsStageStatus[0][:11].upper() == "Ready state".upper():
            self.xps.disableGroup(self.xpsFROGAxis)
        self.updateGUIStatus()       

    def xpsMove(self, btn):
            if self.xpsStageStatus[:11].upper() == "Ready state".upper():
                if btn == "Absolute":
                    if self.ui.c_actenableabs.isChecked():
                        posX = float(self.ui.in_actabsmove.text())
        
                        self.xps.moveAbsolute(self.xpsFROGAxis,posX)
                    else:
                        print('Absolute Move is Disabled')
                elif btn == "SmallForward":
                    posX = float(self.ui.in_actsmallrel.text())
                    self.xps.moveRelative(self.xpsFROGAxis,posX)
                elif btn == "SmallBack":
                    posX = float(self.ui.in_actsmallrel.text())
                    self.xps.moveRelative(self.xpsFROGAxis,-1*posX)
                elif btn == "LargeForward":
                    posX = float(self.ui.in_actlargerel.text())
                    self.xps.moveRelative(self.xxpsFROGAxis,posX)
                elif btn == "LargeBack":
                    posX = float(self.ui.in_actlargerel.text())
                    self.xps.moveRelative(self.xpsFROGAxis,-1*posX)
                else:
                    print('Error: \'%s\' is an invalid entry')
            else:
                print("Stage not ready to move")

    def updatePosition(self):
        if self.xps:
            self.ui.out_actcurrentpos.setText('%0.6f mm'%(self.xps.getStagePosition(self.xpsFROGAxis)))
            self.ui.in_actstatus.setText(self.xps.getStageStatus(self.xpsFROGAxis))

    def updateXPSTravelLimits(self):
        xpsMinLim = self.ui.in_actminlim
        xpsMaxLim = self.ui.in_actmaxlim
        #main code
        time.sleep(.1)

        try:
            limit = float(xpsMinLim.text())
            if limit < 0 or limit > 50:
                print("Invalid minimum limit")
                xpsMinLim.setText(str(self.xps.getminLimit(self.xpsFROGAxis)))
            else:
                self.xps.setminLimit(self.xpsFROGAxis,limit)
        except:
            pass
            
        try:
            limit = float(xpsMaxLim.text())
            if limit < 0 or limit > 50:
                
                print("Invalid maximum limit")
                xpsMaxLim.setText(str(self.xps.getmaxLimit(self.xpsFROGAxis)))
            else:
                self.xps.setmaxLimit(self.xpsFROGAxis,limit)
        except:
            pass

    def updateGUIStatus(self):
        self.xpsStageStatus = self.xps.getStageStatus(self.xpsFROGAxis)
        if self.xpsStageStatus == "Not initialized state" or self.xpsStageStatus == "Not initialized state due to a GroupKill or KillAll command":
            self.ui.p_actinit.setEnabled(True)
            self.ui.p_acthome.setEnabled(False)
            self.ui.p_actenable.setEnabled(False)
            self.ui.p_actabsmove.setEnabled(False)
            self.ui.p_actsmallback.setEnabled(False)
            self.ui.p_actsmallforward.setEnabled(False)
            self.ui.p_actlargeback.setEnabled(False)
            self.ui.p_actlargeforward.setEnabled(False)
            self.ui.in_actstatus.setText("Not Initialized")

        elif self.xpsStageStatus == "Not referenced state":
            self.ui.p_actinit.setEnabled(False)
            self.ui.p_acthome.setEnabled(True)
            self.ui.p_actenable.setEnabled(False)
            self.ui.p_actabsmove.setEnabled(False)
            self.ui.p_actsmallback.setEnabled(False)
            self.ui.p_actsmallforward.setEnabled(False)
            self.ui.p_actlargeback.setEnabled(False)
            self.ui.p_actlargeforward.setEnabled(False)
            self.ui.in_actstatus.setText("Not Homed")
            
        elif self.xpsStageStatus == "Disabled state":         
            self.ui.p_actinit.setEnabled(False)
            self.ui.p_acthome.setEnabled(False)
            self.ui.p_actenable.setEnabled(True)
            self.ui.p_actabsmove.setEnabled(False)
            self.ui.p_actsmallback.setEnabled(False)
            self.ui.p_actsmallforward.setEnabled(False)
            self.ui.p_actlargeback.setEnabled(False)
            self.ui.p_actlargeforward.setEnabled(False)
            self.ui.in_actstatus.setText("Disabled state")
            
        elif self.xpsStageStatus[:11].upper() == "Ready state".upper():
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

    def stopBtn(self):
        if self.xps:
            if self.xpsStageStatus[:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[0])

        sys.exit(0)

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    qdarktheme.setup_theme()
    application = pyFROG_App()
    application.show()
    sys.exit(app.exec_())  
