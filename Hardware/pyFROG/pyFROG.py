import pandas as pd
import h5py as h5
import time, sys
import pyqtgraph as pg
import numpy as np
from scipy import constants
from scipy.signal import find_peaks, peak_widths

from matplotlib.pyplot import draw, pause
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtCore, QtGui, QtWidgets
import qdarktheme

sys.path.append('C:/Users/R2D2/Documents/CODE/Github/HusseinLab_UltrafastPlasmaScience/Hardware')
sys.path.append('C:/Users/nfbei/Documents/Research/Code/Github/HusseinLab_UltrafastPlasmaScience/Hardware')

from pyvisa import ResourceManager
from instrumental import instrument, list_instruments
from pyFROG_GUI_v2 import Ui_MainWindow
from XPS.XPS import XPS

class ThorlabsSpecThread(QtCore.QThread):
    beep=QtCore.pyqtSignal(object)

    def __init__(self,exposureTime):
        super(ThorlabsSpecThread, self).__init__()
        #Spectrometer initialization
        rm = ResourceManager()
        res = rm.list_resources('?*::?*')
        
        if res:
            paramsets = list_instruments()
            self.spec = instrument(paramsets[0],reopen_policy = "reuse")# thorlabs ccs200

            self.running = False
            self.wave = self.spec._wavelength_array
            self.spec.set_integration_time(f'{exposureTime} ms')

            self.spec.start_single_scan()
            self.intensity = self.spec.get_scan_data()

    def __del__(self):
        self.wait()

    def run(self):
        self.running = True
        self.is_paused = False
        self.spec.start_continuous_scan()
        while self.running:
            if self.spec:
                    self.intensity = np.array(self.spec.get_scan_data())
                    self.beep.emit(self.intensity)
                    time.sleep(0.001)
            while self.is_paused:
                time.sleep(0.01)
        self.spec.stop_and_clear()

    def stop(self):
        self.running = False
    
    def pause(self):
        self.spec.stop_and_clear()
        self.is_paused = True
    
    def resume(self):
        self.spec.start_continuous_scan()
        self.is_paused = False

    def getWavelength(self):
        return self.wave
    
    def getIntensity(self):
        return self.intensity
    
    def updateThorlabsParameters(self,val,param = None):
        '''Note this function is causing crashing at the moment. Haven't had time to debug it.'''
        self.pause()
        if param == "integrationTime":
            if self.spec:
                self.spec.set_integration_time(f'{val} ms')
                print(self.spec.get_integration_time())
        self.resume()

class FROGTraceThread(QtCore.QThread):
    beep=QtCore.pyqtSignal(object)
    finished = QtCore.pyqtSignal()
    moveXPS=QtCore.pyqtSignal(object)
    
    def __init__(self):
        super(FROGTraceThread, self).__init__()
        self.running = False
        self.wave, self.intensity = None, None
        self.trace = None
        
    def configureTrace(self,wave,intensity,num_steps,actstep):
        self.wave = wave
        self.intensity = intensity
        self.num_steps = num_steps
        self.actstep = actstep
        self.trace = np.zeros((num_steps,len(self.wave)))

    def setIntensity(self,intensity):
        self.intensity = intensity

    def run(self):
        for ii in range(self.num_steps):
            time.sleep(0.1)
            self.trace[ii] = self.intensity
            self.beep.emit(self.trace)
            self.moveXPS.emit(self.actstep)

        self.finished.emit()

class pyFROG_App(QtWidgets.QMainWindow):
    def __init__(self):
        super(pyFROG_App,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.threadpool = QtCore.QThreadPool()

        self.xps, self.spec = None, None
        self.intensity, self.trace = None, None
        self.trace_bkg = None
        self.ThorlabsThread, self.FROGTraceThread = None, None

        #GUI Interactions
        self.ui.in_scanlen.setText('1000')
        self.ui.in_scanstepnumbers.setText('250')
        self.ui.in_scanstepsize.setText('4.0')
        self.updateScanParameters(param='scanLength')
        
        self.ui.in_scanlen.textChanged.connect(lambda: self.updateScanParameters(param='scanLength'))
        self.ui.in_scanstepnumbers.textChanged.connect(lambda: self.updateScanParameters(param='numberSteps'))
        self.ui.in_scanstepsize.textChanged.connect(lambda: self.updateScanParameters(param='stepSize'))

        self.ui.ConnectXPS.clicked.connect(self._initXPS)
        self.ui.ConnectThorlabs.clicked.connect(self._initThorlabs)
        self.ui.in_specexposure.textChanged.connect(lambda: self.ThorlabsThread.updateThorlabsParameters(self.ui.in_specexposure.text(),param ="integrationTime"))

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
        self.ui.p_savescan.clicked.connect(self.saveFROG)
        self.ui.p_bkgscan.clicked.connect(lambda: self.saveFROG(bkg = True))

        self.FROGTraceThread = FROGTraceThread()
        self.FROGTraceThread.beep.connect(self.updateTracePlot)
        self.FROGTraceThread.finished.connect(self.completeFROG)

        #Timer
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updatePosition)
        self.timer.start()

        self.navi_toolbar = NavigationToolbar(self.ui.frogTracePlot, self)
        self.ui.verticalLayout.insertWidget(0,self.navi_toolbar)

        self.navi_toolbar_2 = NavigationToolbar(self.ui.alignmentPlot, self)
        self.ui.verticalLayout_2.insertWidget(0,self.navi_toolbar_2)

    def _initXPS(self):
        try:
            self.xps = XPS(str(self.ui.in_actip.text()))
            self.xpsGroupNames = self.xps.getXPSStatus()
            self.ui.in_groupname.clear()
            self.ui.in_groupname.addItems(list(self.xpsGroupNames.keys()))
            self.xpsAxes = [str(self.ui.in_groupname.currentText())]
            self.xpsFROGAxis = self.xpsAxes[0]

            self.xps.setGroup(self.xpsFROGAxis)
            self.xpsStageStatus = self.xps.getStageStatus(self.xpsFROGAxis)
            self.updateGUIStatus()

        except AttributeError:
            self.xps = None

    def _initThorlabs(self):
        #Spectrometer initialization
        self.ThorlabsThread = ThorlabsSpecThread(self.ui.in_specexposure.text())
        self.wave = self.ThorlabsThread.getWavelength()
        self.intensity = self.ThorlabsThread.getIntensity()
        self.ui.alignmentPlot.axes.cla()
        self.alignPlot, = self.ui.alignmentPlot.axes.plot(self.wave,self.intensity)
        self.ui.alignmentPlot.axes.set_xlabel("Wavelength [nm]")
        self.ui.alignmentPlot.axes.set_ylabel("Intensity [a.u.]")
        self.ui.alignmentPlot.axes.set_ylim([0,1])

        self.ThorlabsThread.beep.connect(self.updateIntensity)
        self.ThorlabsThread.start()

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
        self.updateXPSTravelLimits()

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
                    self.xps.moveRelative(self.xpsFROGAxis,posX)
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

        limit = float(xpsMinLim.text())
        if limit < 0 or limit > 50:
            print("Invalid minimum limit")
            xpsMinLim.setText(str(self.xps.getminLimit(self.xpsFROGAxis)))
        else:
            self.xps.setminLimit(self.xpsFROGAxis,limit)
            
        limit = float(xpsMaxLim.text())
        if limit < 0 or limit > 50:
            
            print("Invalid maximum limit")
            xpsMaxLim.setText(str(self.xps.getmaxLimit(self.xpsFROGAxis)))
        else:
            self.xps.setmaxLimit(self.xpsFROGAxis,limit)

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

    def updateIntensity(self,intensity):
        self.intensity = intensity
        self.updateAlignmentPlot()
        if self.FROGTraceThread:
            self.FROGTraceThread.setIntensity(intensity)
            
    def initializeTracePlot(self):
        self.ui.frogTracePlot.axTrace.cla()
        self.ui.frogTracePlot.ax_autoconv.cla()
        self.ui.frogTracePlot.ax_autocorr.cla()

        self.trace = np.zeros((self.num_steps,len(self.wave)))
        autocorr = np.sum(self.trace,axis = 1)
        autoconv = np.sum(self.trace,axis = 0)

        self.im = self.ui.frogTracePlot.axTrace.imshow(self.trace.T,aspect = 'auto',origin = 'lower',vmin = 0, vmax = np.amax(self.intensity),extent = [self.delay[0],self.delay[-1],self.wave[0],self.wave[-1]])
        self.autoconvPlot, = self.ui.frogTracePlot.ax_autoconv.plot(autoconv,self.wave)
        self.autocorrPlot, = self.ui.frogTracePlot.ax_autocorr.plot(self.delay,autocorr) 

        self.ui.frogTracePlot.ax_autocorr.set_xlim([self.delay[0],self.delay[-1]])
        self.ui.frogTracePlot.ax_autoconv.set_ylim([self.wave[0],self.wave[-1]])
        self.ui.frogTracePlot.ax_autoconv.set_title("Autoconvolution")
        self.ui.frogTracePlot.ax_autocorr.set_title("Autocorrelation")
        self.ui.frogTracePlot.ax_autocorr.xaxis.set_major_formatter(self.ui.frogTracePlot.nullfmt)
        self.ui.frogTracePlot.ax_autoconv.yaxis.set_major_formatter(self.ui.frogTracePlot.nullfmt)
        self.ui.frogTracePlot.fig.canvas.draw()    

    def updateTracePlot(self,trace):
        self.trace = trace
        self.autocorr = np.sum(trace,axis = 1)
        self.autoconv = np.sum(trace,axis = 0)
        self.autoconvPlot.set_xdata(self.autoconv)
        self.autocorrPlot.set_ydata(self.autocorr)
        self.ui.frogTracePlot.ax_autocorr.set_ylim([0,np.amax(self.autocorr)])
        self.ui.frogTracePlot.ax_autoconv.set_xlim([0,np.amax(self.autoconv)])
        self.im.set_data(trace.T)
        self.im.set_clim(vmin=0, vmax = np.amax(trace))
        self.ui.frogTracePlot.fig.canvas.draw()

    def updateAlignmentPlot(self):
        self.alignPlot.set_ydata(self.intensity)
        self.ui.alignmentPlot.fig.canvas.draw()
        pause(.01)  # give the gui time to process the draw events

    def acquireTrace(self):
        self.num_steps = int(self.ui.in_scanstepnumbers.text())
        scanLength = float(self.ui.in_scanlen.text())

        self.delay = np.linspace(-0.5*scanLength,0.5*scanLength,self.num_steps)
        self.actsteps = self.delay/2*constants.c*1e-12 #convert to fs from mm
        self.actstep = float(round(self.actsteps[1]-self.actsteps[0],4))

        scanParams = [self.wave,self.intensity,self.num_steps,self.actstep]
        self.initializeTracePlot()

        if self.xps and self.xpsStageStatus[:11].upper() == "Ready state".upper():
            pos = round(self.xps.getStagePosition(self.xpsFROGAxis),4)
            self.xpsMove('LargeBack')
            self.xps.moveAbsolute(self.xpsFROGAxis,pos+round(self.actsteps[0],4))

            self.FROGTraceThread.configureTrace(*scanParams)
            self.FROGTraceThread.moveXPS.connect(lambda: self.xps.moveRelative(self.xpsFROGAxis, self.actstep))
            self.FROGTraceThread.start()
        else:
            print("XPS is not ready to perform scan")

    def completeFROG(self):
        print("FROG is done")
        self.FROGTraceThread.wait()
        peaks,_ = find_peaks(self.autocorr,distance=len(self.delay))
        results_half = peak_widths(self.autocorr,peaks,rel_height=0.5)[0]
        autocorr_val = results_half[0]*(self.delay[1]-self.delay[0])
        tempFWHM = autocorr_val/np.sqrt(2)

        self.ui.frogTracePlot.axTrace.text(1.05, 1.49, f'Autocorrelation: {autocorr_val:.1f} fs\nTemporal FWHM: {tempFWHM:.1f} fs', transform=self.ui.frogTracePlot.axTrace.transAxes, fontsize=10,
                verticalalignment='top')
        self.ui.frogTracePlot.fig.canvas.draw()
        
        if self.ui.c_scanautosave.isChecked():
            print("Autosaving FROG")
            self.saveFROG()
        else:
            print("Not autosaving FROG")

    def saveFROG(self,bkg = False):
        dataDict = {'Delay': self.delay, 'Wavelength':self.wave, 'Trace':self.trace}
        if bkg:
            saveFile = f'{self.ui.in_scansavedir.text()}\\{self.ui.in_tracebasename.text()}_bkg_{time.strftime("%Y%m%d-%H%M%S")}'
            self.trace_bkg = self.trace
        else:
            saveFile = f'{self.ui.in_scansavedir.text()}\\{self.ui.in_tracebasename.text()}_{time.strftime("%Y%m%d-%H%M%S")}'

        with h5.File(f'{saveFile}.h5', 'w') as h5file:
            for key, item in dataDict.items():
                # note that not all variable types are supported but string and int are
                h5file[key] = item

    def stopBtn(self):
        if self.xps:
            if self.xpsStageStatus[:11].upper() == "Ready state".upper():
                self.xps.disableGroup(self.xpsAxes[0])
        if self.spec:
            if self.ThorlabsThread:
                self.ThorlabsThread.stop()
            self.spec.close()
        sys.exit(0)

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    #qdarktheme.setup_theme()
    application = pyFROG_App()
    application.show()
    sys.exit(app.exec_())  
