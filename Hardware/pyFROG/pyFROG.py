from pyFROG_GUI import Ui_MainWindow
#from Newport_XPS.HelperClasses.XPS import XPS
import pandas as pd
import time
import pyqtgraph as pg
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

class pyFROG_App(QtWidgets.QMainWindow):
    def __init__(self):
        super(pyFROG_App,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.threadpool = QtCore.QThreadPool()

        #GUI Interactions
        self.ui.in_scanlen.setText('0.01')
        self.ui.in_scanstepnumbers.setText('10')
        self.ui.in_scanstepsize.setText('0.01')
        self.updateScanParameters(param='scanLength')
        
        self.ui.in_scanlen.textChanged.connect(lambda: self.updateScanParameters(param='scanLength'))
        self.ui.in_scanstepnumbers.textChanged.connect(lambda: self.updateScanParameters(param='numberSteps'))
        self.ui.in_scanstepsize.textChanged.connect(lambda: self.updateScanParameters(param='stepSize'))

        self.ui.ConnectXPS.clicked.connect(self._initXPS)
        self.ui.ConnectThorlabs.clicked.connect(self.initThorlabs)

    def _initXPS(self):
        #XPS Initialization
        self.xpsAxes = [str(self.ui.in_groupname.currentText())]
        #self.xps = XPS()
        self.xpsGroupNames = None#self.xps.getXPSStatus()
        self.ui.in_groupname.clear()
        self.ui.in_groupname.addItems(list(self.xpsGroupNames.keys()))
        self.xps.setGroup(self.xpsAxes[0])
        #self.xpsStageStatus = self.xps.getStageStatus(self.)#["Not initialized state"]
        #self.x_xps.getStageStatus(self.x_axis)

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
        #self.ui.canvas.axes
    
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
    import sys
    app = QtWidgets.QApplication(sys.argv)
    application = pyFROG_App()
    application.show()
    sys.exit(app.exec_())  
