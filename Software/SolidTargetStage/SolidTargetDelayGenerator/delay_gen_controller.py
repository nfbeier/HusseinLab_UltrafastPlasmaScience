#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 16:21:51 2025

@author: christina
"""

from PyQt5 import QtWidgets, uic, QtGui, QtCore
#import instruments as ik
import quantities as pq
import json
import time, sys

from delay_gen_gui import Ui_MainWindow

# When editing locally
sys.path.insert(0,'/Users/christina/Documents/github/HusseinLab_UltrafastPlasmaScience/Software/SolidTargetStage/SolidTargetDelayGenerator') 

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
  
            
            

       

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = MainWindow()
    application.show()
    sys.exit(app.exec_()) 