# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 19:06:34 2022

@author: Nick
"""

import sys, os, glob, sif_parser, cv2, matplotlib
import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    
cmap_bella = matplotlib.colors.LinearSegmentedColormap.from_list('cmap_bella',
                                        ['white' , 'blue', 'red', 'yellow' ], 201)

def add_colorbar(p, ax, height = 48, bottom = 0., label = None ):

    ax_inset = inset_axes(ax,
               width="2%", # width = 10% of parent_bbox width
               height="{}%".format(height), # height : 50%
               loc=3,
               bbox_to_anchor=(1.02, bottom, 1, 1),
               bbox_transform=ax.transAxes,
               borderpad=0,
               )

    plt.colorbar(p, cax=ax_inset, label = label)

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100,number_of_subplots = 1, number_of_columns = 3):
        self.fig = Figure(figsize=(width,height), dpi=dpi)
        number_of_rows = 3
            
        if number_of_subplots < 3:
            number_of_columns = number_of_subplots
            
        #elif number_of_subplots % number_of_columns != 0:
        #    number_of_rows = number_of_subplots // number_of_columns 
        #    number_of_rows += 1  
        print(number_of_rows)
        
        # add every single subplot to the figure with a for loop
        self.axs = []
        for k in range(3*number_of_subplots):
          ax = self.fig.add_subplot(number_of_rows,number_of_columns,k + 1)
          ax.set_xticks([])
          ax.set_yticks([])
          self.axs.append(ax)
        
        super(MplCanvas, self).__init__(self.fig)


class DAQ_Window(QtWidgets.QMainWindow):
    def __init__(self, _DAQSetup):
        super(DAQ_Window, self).__init__()
        
        self._DAQSetup = _DAQSetup
        self.shotNum = 1
        self.shotDict = {}
        self.setupGUI()
        
    def setupGUI(self):
        self.mainWidget = QtWidgets.QWidget(self) 
        self.setCentralWidget(self.mainWidget)
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)
        self.hLayout = QtWidgets.QHBoxLayout()
        self.setMinimumSize(1600, 600)
        
        totalPlots = self._DAQSetup.ui.numberDiagnostics.value()
        self.sc = MplCanvas(self, width=24,height = 9, dpi=200,\
                        number_of_subplots = totalPlots, number_of_columns = 3)
            
        for diagNum,diag in enumerate(self._DAQSetup.diagInfo["Diagnostic Name"]):
            if diag is not None:
                self.sc.axs[diagNum].set_title(diag)
        
        self.sc.fig.subplots_adjust(top=0.9, bottom=0.05, left=0.025,
            right=0.925,hspace=0.2,wspace=0.3)
        
        self.show()   
        
        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.sc, self)
        
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.nextShot = QtWidgets.QPushButton()
        self.nextShot.setFont(font)
        self.nextShot.setObjectName("nextShot")

        #layout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(toolbar)
        self.mainLayout.addWidget(self.sc)
        self.mainLayout.addWidget(self.nextShot)
        
        #Create spinboxes for comparing two previous shots
        self.oldShot1 = QtWidgets.QSpinBox()
        self.oldShot2 = QtWidgets.QSpinBox()
        
        self.label_1 = QtWidgets.QLabel()
        self.label_1.setEnabled(True)
        self.label_2 = QtWidgets.QLabel()
        self.label_2.setEnabled(True)
        self.label_1.setFont(font)
        self.label_1.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        
        self.previousShots = QtWidgets.QPushButton()
        self.previousShots.setFont(font)
        self.previousShots.setObjectName("previousShots")
        
        self.hLayout.addWidget(self.label_1)
        self.hLayout.addWidget(self.oldShot1)
        self.hLayout.addWidget(self.label_2)
        self.hLayout.addWidget(self.oldShot2)
        self.hLayout.addWidget(self.previousShots)
        self.mainLayout.addLayout(self.hLayout)
        
        _translate = QtCore.QCoreApplication.translate     
        self.mainWidget.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.nextShot.setText(_translate("MainWindow", "Next Shot"))
        self.label_1.setText(_translate("MainWindow","Enter Previous Shot 1:"))
        self.label_2.setText(_translate("MainWindow","Enter Previous Shot 2:"))
        self.previousShots.setText(_translate("MainWindow", "Update Previous Shots"))
        
        self.nextShot.clicked.connect(self.updatePlots)
        self.previousShots.clicked.connect(self.updatePrevious)
        
        self.prevShot = [None]*self._DAQSetup.ui.numberDiagnostics.value()
        self.prevTime = [None]*self._DAQSetup.ui.numberDiagnostics.value()
        self.updatePlots = [False]*self._DAQSetup.ui.numberDiagnostics.value()
        self.plots = [None]*self._DAQSetup.ui.numberDiagnostics.value()
    
    def pullNewFiles(self, diagNum, file_Path,file_Type):
        list_of_files = sorted(glob.glob(r'%s/*%s*'%(file_Path,file_Type)), key=os.path.getmtime)
        num_Files = -1*int(self._DAQSetup.diagInfo["Shots per Save"][diagNum])
        if len(list_of_files) > 0:
            latest_files = list_of_files[num_Files:]
            latest_times = [os.path.getmtime(latest_file) for latest_file in latest_files]
        else:
            latest_files = None
            latest_times = None
        if self.shotNum == 1 and latest_files:
            self.prevShot[diagNum] = latest_files
            self.prevTime[diagNum] = latest_times
            self.updatePlots[diagNum] = True
        elif latest_files:
            if (latest_files != self.prevShot[diagNum]) or (latest_times != self.prevTime[diagNum]): 
                #Checks to see if the filename or the file modified time is changed from previous latest file
                self.prevShot[diagNum] = latest_files
                self.prevTime[diagNum] = latest_times
                self.updatePlots[diagNum] = True
            else:
                #This indicates that the new file has both the same file name and the same modified time (data did not update!)
                self.prevShot[diagNum] = latest_files
                self.prevTime[diagNum] = latest_times
                self.updatePlots[diagNum] = False
                
        return latest_files, latest_times
    
    def updatePlots(self):
        for diagNum,diagName in enumerate(self._DAQSetup.diagInfo["Diagnostic Name"]):
            file_Path = self._DAQSetup.diagInfo["File Path"][diagNum]
            file_Type = self._DAQSetup.diagInfo["File Type"][diagNum]
            
            latest_files, latest_times = self.pullNewFiles(diagNum,file_Path,file_Type)
            
            shotData = []
            if self.updatePlots[diagNum] == True:
                for shot in latest_files:
                    if file_Type == '.sif':
                        data, info = sif_parser.np_open(shot)
                        im = data[0]
                        shotData.append(im)
                        if self._DAQSetup.backgroundData[diagName] is None:
                            pass
                        else:
                            im = self._DAQSetup.backgroundData[diagName] - im
                    else:
                        im = cv2.imread(shot,0)
                        shotData.append(im)
                        if self._DAQSetup.backgroundData[diagName] is None:
                            pass
                        else:
                            im -= self._DAQSetup.backgroundData[diagName]
                        
                if self.shotNum == 1:  
                    self.plots[diagNum] = self.sc.axs[diagNum].imshow(im,aspect="auto",cmap = "inferno_r")
                    self.sc.axs[diagNum].set_title(r"%s: Shot %d"%(diagName,self.shotNum))
                    add_colorbar(self.plots[diagNum],self.sc.axs[diagNum],height = 100)
                    self.sc.fig.canvas.draw()
                else:
                    self.plots[diagNum].set_data(im)
                    self.sc.axs[diagNum].draw_artist(self.plots[diagNum])
                    self.sc.axs[diagNum].set_title(r"%s: Shot %d"%(diagName,self.shotNum))
                    self.sc.fig.canvas.blit() 
                    
                self.shotDict[diagName] = shotData
                
            else:
                self.shotDict[diagName] = None
                self.sc.axs[diagNum].set_title(r"%s: Shot Not Updated" % diagName)
                self.sc.fig.canvas.blit()      
        
        if any(self.updatePlots):
            self.saveData()
        else:
            print("No Shots were Updated")            

    def saveData(self):
        saveFileName = r"%sShot%05d.h5"%(self._DAQSetup.saveData,self.shotNum)
        counter = 0
        while os.path.isfile(saveFileName):
            counter += 1
            saveFileName = r"%sShot%05d_%d.h5"%(self._DAQSetup.saveData,self.shotNum,counter)
        df = pd.Series(self.shotDict)
        df.to_hdf(saveFileName,key='s', mode='w')
        self.sc.fig.savefig(r"%sShot%05d.png"%(self._DAQSetup.savePlot,self.shotNum))
        self.shotNum += 1
    
    def updatePrevious(self):
        print("Gotcha")
        for row, shotNum in enumerate([self.oldShot1.value(),self.oldShot2.value()]):
            saveFileName = r"%sShot%05d.h5"%(self._DAQSetup.saveData,shotNum)
            if os.path.isfile(saveFileName):
                previous_data = pd.read_hdf(saveFileName,key='s', mode='r')
                for diagNum, diagName in enumerate(previous_data.keys()):
                    data = previous_data[diagName][-1]
                    if self._DAQSetup.backgroundData[diagName] is None:
                        pass
                    elif self._DAQSetup.diagInfo["File Type"][diagNum] == ".sif":
                        data = self._DAQSetup.backgroundData[diagName] - data
                    else:
                        data -= self._DAQSetup.backgroundData[diagName]
                    plotNum = diagNum+3*(row+1)
                    plot = self.sc.axs[plotNum].imshow(data,aspect="auto",cmap = "inferno_r")
                    add_colorbar(plot,self.sc.axs[plotNum],height = 100)
                    self.sc.fig.canvas.draw()
            else:
                print("Previous Shot Number %d Does Not Exist"%shotNum)
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = DAQ_Window()
    application.show()
    app.exec_() 