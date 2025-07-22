# -*- coding: utf-8 -*-
"""
Created on Tue Sep  5 14:17:32 2023

@author: Nick
"""

from PyQt5 import QtCore, QtWidgets
import sys, torch, time
from PyQt5.QtWidgets import QMainWindow
from sourceReconstruct_GUI import Ui_MainWindow
import numpy as np
import pyqtgraph as pg
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from reconstructionAlgorithm import *
import sif_parser,cv2

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(imageAxisOrder='row-major')
     

class Watch_Thread(QtCore.QThread):
    updated = QtCore.pyqtSignal(str)
    
    class MyHandler(FileSystemEventHandler):
        def __init__(self, eventThread, case_sensitive=False):
            super(FileSystemEventHandler, self).__init__()
            self.eventThread = eventThread
            self._case_sensitive = case_sensitive
            
            
        def process(self, event):
			# the file will be processed here
			#print event.src_path, event.event_type
			#event_string = str(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())) + ' : '
            event_string = str(event.src_path)
			#print event_string
            self.eventThread.updated.emit(event_string)	

        def on_created(self, event):
            self.process(event)

    def run(self):
        observer = Observer()
        observer.schedule(self.MyHandler(self), path=self.watchDir)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("Observer Stopped")

        observer.join()
        
    def updateWatchDirectory(self,watchDir):
        self.watchDir = watchDir
        print("Updated directory to")
        print(self.watchDir)

class reconstruciton_Thread(QtCore.QThread):
    criticalEnergy = QtCore.pyqtSignal(str)
    
    def __init__(self,minAlg):
        super(reconstruciton_Thread,self).__init__()
        self.minAlg = minAlg
        self.NN = None
        self.variables = None
        self.stop = False
        
        self.X_mean,self.X_std = None, None
        self.Y_mean,self.Y_std = None, None
        
    def updateData(self,data_counts):
        self.data_counts = data_counts
        
    def updateReconstructionAlgorithm(self,algorithm):
        self.algorithm = algorithm
    
    def loadNeuralNetwork(self,NN,variables,filterPack):
        self.NN = NN
        self.variables = variables
        
        if filterPack == "StepWedgeFilters":
            if self.variables is True:
                self.Y_mean,self.Y_std = np.loadtxt("HelperFiles\StepWedgeFilterPack\OneVariableNormalization_Y.txt",unpack = True)
            else:
                self.X_mean,self.X_std = np.loadtxt("HelperFiles\StepWedgeFilterPack\TwoVariableNormalization_X.txt",unpack = True)
                self.Y_mean,self.Y_std = np.loadtxt("HelperFiles\StepWedgeFilterPack\TwoVariableNormalization_Y.txt",unpack = True)
        else:
            if self.variables is True:
                self.Y_mean,self.Y_std = np.loadtxt("HelperFiles\RossPairFilterPack\OneVariableNormalization_Y.txt",unpack = True)
            else:
                self.X_mean,self.X_std = np.loadtxt("HelperFiles\RossPairFilterPack\TwoVariableNormalization_X.txt",unpack = True)
                self.Y_mean,self.Y_std = np.loadtxt("HelperFiles\RossPairFilterPack\TwoVariableNormalization_Y.txt",unpack = True)
        
    def run(self):
        try:
            while True:
                time.sleep(1)
                
                if self.algorithm == 0:
                    if self.variables:
                        x_norm = torch.tensor(self.data_counts/np.average(self.data_counts), dtype=torch.float32)
                        y_pred = self.NN(x_norm).detach().numpy()[0]
                        
                        eCrit = self.NN.deStandardizeData(y_pred,self.Y_mean,self.Y_std)
                        
                    else:
                        x_standardized = (self.data_counts-self.X_mean)/self.X_std
                        x_standardized = torch.tensor(x_standardized, dtype=torch.float32)
                        y_pred = self.NN(x_standardized).detach().numpy()
                        
                        eCrit, Amp = self.NN.deStandardizeData(y_pred,self.Y_mean,self.Y_std)
                    
                else:
                    eCrit = self.minAlg.calculateEcrit(self.data_counts/np.average(self.data_counts))
                
                self.criticalEnergy.emit(str(eCrit))
                if self.stop:
                    break
        except Exception as error:
            print("Reconstruction Stopped")
            print(error)
            

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
  
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.minAlg, self.NN = None, None
        self.watcher_Thread, self.reconstruct_Thread = None, None
        self.data_directory = r"D:\Research\UAlberta\Research\Data\Neural Network Training\September 2023\TestingReconstructionProgram\DataFolder"
        self.rois, self.eCrits = [], []

        self.ui.dataDir.setText(self.data_directory)
        
        imagedata = np.random.rand(256,256)
        
        self.vb = self.ui.plotWidget.addViewBox(lockAspect = True,invertY = True)
        self.ROI_im = pg.ImageItem(imagedata)
        self.ROI_im.setColorMap(pg.colormap.getFromMatplotlib("inferno"))
        self.vb.addItem(self.ROI_im)

        cbar = pg.HistogramLUTItem(image=self.ROI_im)
        cbar.gradient.loadPreset('inferno')
        self.ui.plotWidget.addItem(cbar,0,1)
        
        self.p1 = self.ui.plotWidget.addPlot(2,0)
        self.p1.setLabel("bottom","Filter Number", size = "24pt")
        self.p1.setLabel("left","Integrated Intensity", size = "24pt")
        
        self.p2 = self.ui.reconstructWidget.addPlot()
        self.p2.setLabel("bottom","Iteration Number", size = "24pt")
        self.p2.setLabel("left","Critical Energy", size = "24pt")
        self.eCritPlot = self.p2.plot()
        
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.browse.clicked.connect(self.browseFiles)
        self.ui.acquireImages.clicked.connect(self.updatePlots)
        self.ui.reconstructSpectra.clicked.connect(self.reconstruct)
        self.ui.reconstructAlgorithmComboBox.currentTextChanged.connect(self.updateAlgorithm)
        self.ui.NN_NormalizeCheck.stateChanged.connect(self.loadNeuralNetwork)
        
    def WatchdogReceiver(self, latest_file):
        if latest_file:
            if latest_file.endswith('.sif'):
                data, info = sif_parser.np_open(latest_file)
                data = data[0]
            elif latest_file.endswith('.tif'):
                data = cv2.imread(latest_file,0)
            else:
                data = np.loadtxt(latest_file)
            
            self.ROI_im.setImage(data)
            self.ui.avgCountsLabels.setText("Average Counts: %0.1f" %np.average(data))
            
            for roiIdx in range(len(self.rois)):
                data = self.rois[roiIdx].getArrayRegion(self.ROI_im.image, img=self.ROI_im)
                self.rois_curve[roiIdx] = data.mean()
                self.c.setData(self.rois_curve)
                
            self.data_counts = self.rois_curve[:-1] - self.rois_curve[-1]
                
            if self.reconstruct_Thread:
                self.reconstruct_Thread.updateData(self.data_counts)
                
            self.eCrits = []
    
    def reconstructionReceiver(self,eCrit):
        if eCrit:  
            self.eCrits.append(float(eCrit))
            self.ui.criticalEnergy.setText("Critical Energy: %0.1f keV" % round(float(eCrit),1))
            self.ui.avgCriticalEnergy.setText("Average Critical Energy: %0.1f keV" % round(float(np.average(self.eCrits)),1))
            self.eCritPlot.setData(range(len(self.eCrits)),self.eCrits)
    
    def updateROI(self):
        roi_cmap = pg.colormap.getFromMatplotlib("rainbow")
        
        if self.ui.filterPackComboBox.currentText() == "StepWedgeFilters":
            numROI = 9
        else:
            numROI = 12
            
        for i in range(numROI):
            self.rois.append(pg.TestROI([0,  0], [20, 20], pen=roi_cmap[i//3*3.0/numROI],removable = True))
            
        for r in self.rois:
            self.vb.addItem(r)
            r.sigRegionChanged.connect(self.updateRoiPlot)
            
        self.rois_curve = np.zeros(numROI)
        self.c = self.p1.plot(np.arange(1,numROI+1),self.rois_curve,symbol = "o",symbolPen = "k")
    
    def updateRoiPlot(self,roi, data=None):
        roiIdx = self.rois.index(roi)
        if data is None:
            data = roi.getArrayRegion(self.ROI_im.image, img=self.ROI_im)
        if data is not None:
            self.rois_curve[roiIdx] = data.mean()
            self.c.setData(self.rois_curve)
            
        self.data_counts = self.rois_curve[:-1] - self.rois_curve[-1]
            
        if self.reconstruct_Thread:
            self.reconstruct_Thread.updateData(self.data_counts)
    
    def loadNeuralNetwork(self):
        device = torch.device('cpu')
        if self.ui.filterPackComboBox.currentText() == "StepWedgeFilters":
            if self.ui.NN_NormalizeCheck.isChecked():
                self.NN = NeuralNetworkOneVariable_SWF()
                self.NN.load_state_dict(torch.load(r"HelperFiles\StepWedgeFilterPack\OneVariableModel", map_location=device))
            else:
                self.NN = NeuralNetworkTwoVariable_SWF() 
                self.NN.load_state_dict(torch.load(r"HelperFiles\StepWedgeFilterPack\TwoVariableModel", map_location=device))
    
        else:
            if self.ui.NN_NormalizeCheck.isChecked():
                self.NN = NeuralNetworkOneVariable_RPF()
                self.NN.load_state_dict(torch.load(r"HelperFiles\RossPairFilterPack\OneVariableModel", map_location=device))
            else:
                self.NN = NeuralNetworkTwoVariable_RPF()
                self.NN.load_state_dict(torch.load(r"HelperFiles\RossPairFilterPack\TwoVariableModel", map_location=device))
    
        if self.reconstruct_Thread:
            self.reconstruct_Thread.loadNeuralNetwork(self.NN,self.ui.NN_NormalizeCheck.isChecked(),self.ui.filterPackComboBox.currentText())
    
    def updateAlgorithm(self):
        if self.reconstruct_Thread:
            self.reconstruct_Thread.updateReconstructionAlgorithm(self.ui.reconstructAlgorithmComboBox.currentIndex())
    
    def browseFiles(self):
        self.data_directory = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory",r"D:\Research\UAlberta\Research\Data\Neural Network Training\September 2023\TestingReconstructionProgram\DataFolder"))
        self.ui.dataDir.setText(self.data_directory)
        if self.watcher_Thread:
            self.watcher_Thread.updateWatchDirectory(self.data_directory)
    
    def updatePlots(self):
        self.minAlg = minimizationAlgorithm(self.ui.filterPackComboBox.currentText())
        self.updateROI()
        
        self.watcher_Thread = Watch_Thread(self)
        self.watcher_Thread.updated.connect(self.WatchdogReceiver)
        self.watcher_Thread.updateWatchDirectory(self.ui.dataDir.text())
        self.watcher_Thread.start()
        
    def reconstruct(self):
        self.loadNeuralNetwork()
        self.reconstruct_Thread = reconstruciton_Thread(self.minAlg)
        self.reconstruct_Thread.loadNeuralNetwork(self.NN,self.ui.NN_NormalizeCheck.isChecked(),self.ui.filterPackComboBox.currentText())
        self.reconstruct_Thread.criticalEnergy.connect(self.reconstructionReceiver)
        
        self.reconstruct_Thread.updateReconstructionAlgorithm(self.ui.reconstructAlgorithmComboBox.currentIndex())
        self.reconstruct_Thread.updateData(self.data_counts)
        self.reconstruct_Thread.start()
    
    def close(self):
        #if self.watcher_Thread:
        #    self.watcher_Thread.stop = True
        if self.reconstruct_Thread:
            self.reconstruct_Thread.stop = True
        QtWidgets.QApplication.quit()
        #self.close()
        #sys.exit(0)  
        
if __name__ == "__main__":
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    application = MainWindow()
    application.show()
    app.exec_()