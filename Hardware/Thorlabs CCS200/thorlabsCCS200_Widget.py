import numpy as np
from pyvisa import ResourceManager
from instrumental import instrument#, list_instruments
from instrumental.drivers.spectrometers.thorlabs_ccs import list_instruments
import os, sys, time
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pandas as pd
cwd = os.getcwd()
# Check if 'HusseinLab_UltrafastPlasmaScience' is in the components
if 'HusseinLab_UltrafastPlasmaScience' not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")

# Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience', prevent import errors
cwd = os.path.sep.join(cwd.split(os.path.sep)[:cwd.split(os.path.sep).index('HusseinLab_UltrafastPlasmaScience') + 1])

sys.path.insert(0,cwd)

from thorlabsCCS200_GUI import Ui_Form

class SaveThread(QtCore.QThread):
    def __init__(self, scans, template, exposure, shotNumber):
        super(SaveThread, self).__init__()
        self.scans = scans
        self.exposureTime = exposure
        self.shotNumber = shotNumber
        [self.folder, self.fileName, self.date, self.shotTracker] = template
        self.shotDict = {}
        if self.folder == None:
            self.folder = r"D:\Data\Default Save Directory\Flame"
        if self.fileName == None:
            self.fileName = "No_Name"
        if self.date == None:
            self.date = True
 
    def run(self):
        if self.date:
            now = QtCore.QDateTime.currentDateTime()
            nowString = now.toString(QtCore.Qt.ISODate)
            formatDate = nowString.replace(":","").replace("-","").replace("T","_")
            self.fileName = formatDate + "_"+ self.fileName
            self.shotDict = {"Date": formatDate}
        
        if self.shotTracker:
            self.shotDict["Shot Number"] = self.shotNumber 
        self.shotDict["Exposure Time"] = self.exposureTime
        self.shotDict["Experimental Campaign"] = "Testing" 
        self.shotDict["Device"] = "Thorlabs CCS200"              
        self.shotDict["Flame Spectra"] = self.scans
        self.shotDict["Flame Spectra Number"] = len(self.scans)
        
        df = pd.Series(self.shotDict)
        
        if self.shotTracker:
            fullName = r"%s/%s_Shot%05d.h5"%(self.folder,self.fileName,self.shotNumber)
            print(fullName)
            df.to_hdf(fullName,key='s', mode='w')
        else:
            fullName = r"%s/%s.h5"%(self.folder,self.fileName)
            print(fullName)
            df.to_hdf(fullName,key='s', mode='w')
        
        for count,spec in enumerate(self.scans):
            fullName = "%s/%s_%05d.txt" % (self.folder,self.fileName,count)
            print(fullName)
            np.savetxt(fullName,np.column_stack((spec[0],spec[1])),fmt = "%0.7f",delimiter = "\t", header = "Wavelength (nm)\tIntensity")
    
    def __del__(self):
        del self.scans

class ThorlabsSpecThread(QtCore.QThread):
    acquired=QtCore.pyqtSignal(object)

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
                    self.acquired.emit(self.intensity)
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

class thorlabsWidget(QtWidgets.QMainWindow):
    def __init__(self):
        super(thorlabsWidget,self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ThorlabsThread = None

        self.navi_toolbar = NavigationToolbar(self.ui.spectrumPlot, self)
        self.ui.verticalLayout.insertWidget(0,self.navi_toolbar)
        #self.threadpool = QtCore.QThreadPool()

        self.ui.ConnectThorlabs.clicked.connect(self._initThorlabs)
        self.ui.in_specexposure.textChanged.connect(lambda: self.ThorlabsThread.updateThorlabsParameters(self.ui.in_specexposure.text(),param ="integrationTime"))

    def _initThorlabs(self):
        if self.ThorlabsThread:
            print("Thorlabs Spectrometer has already been initialized")
        else:
            #Spectrometer initialization
            self.ThorlabsThread = ThorlabsSpecThread(self.ui.in_specexposure.text())
            self.wave = self.ThorlabsThread.getWavelength()
            self.intensity = self.ThorlabsThread.getIntensity()
            self.ui.spectrumPlot.axes.cla()
            self.alignPlot, = self.ui.spectrumPlot.axes.plot(self.wave,self.intensity)
            self.ui.spectrumPlot.axes.set_xlabel("Wavelength [nm]")
            self.ui.spectrumPlot.axes.set_ylabel("Intensity [a.u.]")
            self.ui.spectrumPlot.axes.set_ylim([0,1])

            self.ThorlabsThread.acquired.connect(self.updateIntensity)
            self.ThorlabsThread.start()     

    def updateAlignmentPlot(self):
        self.alignPlot.set_ydata(self.intensity)
        self.ui.spectrumPlot.fig.canvas.draw()

    def updateIntensity(self,intensity):
        self.intensity = intensity
        self.updateAlignmentPlot()

    def stopBtn(self):
        if self.spec:
            if self.ThorlabsThread:
                self.ThorlabsThread.stop()
            self.spec.close()
        sys.exit(0)

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    #qdarktheme.setup_theme()
    application = thorlabsWidget()
    application.show()
    sys.exit(app.exec_())  
