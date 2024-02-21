import pandas as pd
import time, sys
import pyqtgraph as pg
import numpy as np
from scipy import constants
from matplotlib.pyplot import draw, pause
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from pyvisa import ResourceManager
from PyQt5 import QtCore, QtGui, QtWidgets
import qdarktheme
from instrumental import instrument, list_instruments

sys.path.append('C:/Users/R2D2/Documents/CODE/Github/HusseinLab_UltrafastPlasmaScience/Hardware')
sys.path.append('C:/Users/nfbei/Documents/Research/Code/Github/HusseinLab_UltrafastPlasmaScience/Hardware')

from pyFROG_GUI import Ui_MainWindow
from XPS.XPS import XPS

class ThorlabsSpecThread(QtCore.QThread):
    beep=QtCore.pyqtSignal(object)

    def __init__(self,spec):
        super(ThorlabsSpecThread, self).__init__()
        self.spec = spec
        self.running = False

    def run(self):
        self.running = True
        self.spec.start_continuous_scan()
        while self.running:
            self.intensity = np.array(self.spec.get_scan_data())
            self.beep.emit(self.intensity)

    def stop(self):
        self.running = False
        self.spec.stop_scan

class pyFROG_App(QtWidgets.QMainWindow):
    def __init__(self):
        super(pyFROG_App,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.threadpool = QtCore.QThreadPool()

        self.xps, self.spec = None, None

        #GUI Interactions
        self.ui.in_scanlen.setText('300')
        self.ui.in_scanstepnumbers.setText('100')
        self.ui.in_scanstepsize.setText('3')
        self.updateScanParameters(param='scanLength')
        
        self.ui.in_scanlen.textChanged.connect(lambda: self.updateScanParameters(param='scanLength'))
        self.ui.in_scanstepnumbers.textChanged.connect(lambda: self.updateScanParameters(param='numberSteps'))
        self.ui.in_scanstepsize.textChanged.connect(lambda: self.updateScanParameters(param='stepSize'))

        self.ui.ConnectXPS.clicked.connect(self._initXPS)
        self.ui.ConnectThorlabs.clicked.connect(self._initThorlabs)
        self.ui.in_specexposure.textChanged.connect(lambda: self.updateThorlabsParameters(param ="integrationTime"))

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

        self.ui.p_aquirescan.clicked.connect(self.acquireTrace)

        #Timer
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.updatePosition)
        self.timer.start()

        self.navi_toolbar = NavigationToolbar(self.ui.alignmentPlot, self)
        self.ui.verticalLayout_8.insertWidget(0,self.navi_toolbar)

        self.navi_toolbar_2 = NavigationToolbar(self.ui.frogTracePlot, self)
        self.ui.verticalLayout_6.insertWidget(0,self.navi_toolbar_2)

        #Load old data as reference
        file = r'Hardware\pyFROG\Old Examples\data\frg_trace_1580511001.pkl'
        data = pd.read_pickle(file)
        self.wave = data['wave'][0]
        trace = data['trace'][0]

        timeAxis = np.linspace(-300,300,100)
        self.ui.frogTracePlot.axTrace.imshow(trace.T,aspect = 'auto',origin = 'lower',extent = [timeAxis[0],timeAxis[-1],self.wave[0],self.wave[-1]])
        autocorr = np.sum(trace,axis = 1)
        autoconv = np.sum(trace,axis = 0)
        self.ui.frogTracePlot.ax_autoconv.plot(autoconv,self.wave)
        self.ui.frogTracePlot.ax_autocorr.plot(timeAxis, autocorr)

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

        self.wave = self.spec._wavelength_array
        self.spec.set_integration_time('100 ms')
        print(self.spec.get_integration_time())

        self.spec.start_single_scan()
        self.intensity=np.array(self.spec.get_scan_data())

        self.ui.alignmentPlot.axes.cla()
        self.alignPlot, = self.ui.alignmentPlot.axes.plot(self.wave,self.intensity)
        self.ui.alignmentPlot.axes.set_xlabel("Wavelength [nm]")
        self.ui.alignmentPlot.axes.set_ylabel("Intensity [a.u.]")

        self.ThorlabsThread = ThorlabsSpecThread(self.spec)
        self.ThorlabsThread.beep.connect(self.updateAlignmentPlot)
        self.ThorlabsThread.start()

    def updateThorlabsParameters(self,param = None):
        '''Note this function is causing crashing at the moment. Haven't had time to debug it.'''
        if param == "integrationTime":
            if self.spec:
                intTime = self.ui.in_specexposure.text()
                self.spec.set_integration_time(f'{intTime} ms')

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
        elif self.xpsStageStatus[:11].upper() == "Ready state".upper():
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
            pos = round(self.xps.getStagePosition(self.xpsFROGAxis),4)
            self.ui.out_actcurrentpos.setText(f'{pos:.4f} mm')
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

    def updateAlignmentPlot(self,intensity):
        self.intensity = intensity
        self.alignPlot.set_ydata(self.intensity)
        self.ui.alignmentPlot.fig.canvas.draw()
        pause(.01)  # give the gui time to process the draw events

    def acquireTrace(self,pause=0.005):
            num_steps = int(self.ui.in_scanstepnumbers.text())
            scanLength = float(self.ui.in_scanlen.text())
            step_size = float(self.ui.in_scanstepsize.text())
            
            delay = np.linspace(-0.5*scanLength,0.5*scanLength,num_steps)
            actsteps = round(delay/(2*constants.c),4)
            actstep = actsteps[1]-actsteps[0]

            self.ui.frogTracePlot.ax_autoconv.cla()
            self.ui.frogTracePlot.ax_autocorr.cla()

            trace = np.zeros((num_steps,len(self.wave)))
            autocorr = np.sum(trace,axis = 1)
            autoconv = np.sum(trace,axis = 0)

            im = self.ui.frogTracePlot.axTrace.imshow(trace.T,aspect = 'auto',origin = 'lower',extent = [delay[0],delay[-1],self.wave[0],self.wave[-1]])
            self.autoconvPlot, = self.ui.frogTracePlot.ax_autoconv.plot(autoconv,self.wave)
            self.autocorrPlot, = self.ui.frogTracePlot.ax_autocorr.plot(delay,autocorr) 

            self.ui.frogTracePlot.ax_autocorr.set_xlim([delay[0],delay[-1]])
            self.ui.frogTracePlot.ax_autoconv.set_ylim([self.wave[0],self.wave[-1]])
            self.ui.frogTracePlot.ax_autoconv.set_title("Autoconvolution")
            self.ui.frogTracePlot.ax_autocorr.set_title("Autocorrelation")
            self.ui.frogTracePlot.ax_autocorr.xaxis.set_major_formatter(self.ui.frogTracePlot.nullfmt)
            self.ui.frogTracePlot.ax_autoconv.yaxis.set_major_formatter(self.ui.frogTracePlot.nullfmt)

            self.ui.frogTracePlot.fig.canvas.draw()    

            pos = round(self.xps.getStagePosition(self.xpsFROGAxis),4)
            self.xpsMove('LargeBack')
            self.xps.moveAbsolute(self.xpsFROGAxis,pos-actsteps[0])

            for ii in range(num_steps):
                time.sleep(pause)
                trace[ii] = self.intensity
                autocorr = np.sum(trace,axis = 1)
                autoconv = np.sum(trace,axis = 0)
                self.autoconvPlot.set_ydata(autoconv)
                self.autocorrPlot.set_ydata(autocorr)
                im.setImage(trace)
                self.ui.frogTracePlot.fig.canvas.draw()
                self.xps.moveRelative(self.xpsFROGAxis,actstep)

    def stopBtn(self):
        if self.xps:
            if self.xpsStageStatus[:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[0])

        sys.exit(0)

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    #qdarktheme.setup_theme()
    application = pyFROG_App()
    application.show()
    sys.exit(app.exec_())  
