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


if __name__ == "__main__":
    #from ResultsWindow import Results
    import sys
    app = QtWidgets.QApplication(sys.argv)
    application = pyFROG_App()
    application.show()
    sys.exit(app.exec_())  