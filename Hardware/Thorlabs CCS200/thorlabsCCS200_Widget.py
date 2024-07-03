import numpy as np
from pyvisa import ResourceManager
from instrumental import instrument, list_instruments
import os, sys, time
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

cwd = os.getcwd()
# Check if 'HusseinLab_UltrafastPlasmaScience' is in the components
if 'HusseinLab_UltrafastPlasmaScience' not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")

# Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience', prevent import errors
cwd = os.path.sep.join(cwd.split(os.path.sep)[:cwd.split(os.path.sep).index('HusseinLab_UltrafastPlasmaScience') + 1])

sys.path.insert(0,cwd)

from thorlabsCCS200_GUI import Ui_Form

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

class pyFROG_App(QtWidgets.QMainWindow):
    def __init__(self):
        super(pyFROG_App,self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.navi_toolbar = NavigationToolbar(self.ui.spectrumPlot, self)
        self.ui.verticalLayout.insertWidget(0,self.navi_toolbar)
        #self.threadpool = QtCore.QThreadPool()

    '''def _initThorlabs(self):
        if self.ThorlabsThread:
            print("Thorlabs Spectrometer has already been initialized")
        else:
            #Spectrometer initialization
            self.ThorlabsThread = ThorlabsSpecThread(self.ui.in_specexposure.text())
            self.wave = self.ThorlabsThread.getWavelength()
            self.intensity = self.ThorlabsThread.getIntensity()
            self.ui.alignmentPlot.axes.cla()
            self.alignPlot, = self.ui.alignmentPlot.axes.plot(self.wave,self.intensity)
            self.ui.alignmentPlot.axes.set_xlabel("Wavelength [nm]")
            self.ui.alignmentPlot.axes.set_ylabel("Intensity [a.u.]")
            self.ui.alignmentPlot.axes.set_ylim([0,1])

            self.ThorlabsThread.acquired.connect(self.updateIntensity)
            self.ThorlabsThread.start()'''

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
    application = pyFROG_App()
    application.show()
    sys.exit(app.exec_())  
