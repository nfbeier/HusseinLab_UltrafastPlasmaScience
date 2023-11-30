# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'testGUI.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets
import sys, sif_parser, cv2, os, json
from PyQt5.QtWidgets import QDialog,QMainWindow,QMenu, QFileDialog, QTableWidgetItem
from daq_GUI import Ui_MainWindow
from resultsWindow import DAQ_Window
from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()
  
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.directory = None
        self.defaultValuesPath = r"C:\Users\nfbei\Documents\UofA\Research\Code\Github\DataAcquisition\DAQ\defaultValues.json"
        self.backgroundData = {}
        with open(self.defaultValuesPath, 'r') as openfile:
            # Reading from json file
            self.defaultValues = json.load(openfile)
        
        self.ui.numberDiagnostics.valueChanged.connect(self.add_table)
        self.ui.browse.clicked.connect(self.browseFiles)
        self.ui.confirmSetup.clicked.connect(self.confirmSetup)
        self.ui.exitAction.triggered.connect(self.close)
        self.ui.saveDefaultValuesAction.triggered.connect(self.save_DefaultValues)
    
        self.load_DefaultValues()
        
    def load_DefaultValues(self):
        rowDiff = self.ui.numberDiagnostics.value() - self.defaultValues["tableRows"]
        if rowDiff < 0:
            for i in range(-1*rowDiff):
                self.ui.numberDiagnostics.setValue(self.ui.numberDiagnostics.value()+1)
        elif rowDiff > 0:
            for i in range(rowDiff):
                self.ui.numberDiagnostics.setValue(self.ui.numberDiagnostics.value()-1)
        
        self.directory = self.defaultValues["saveDirectory"]  
        self.ui.saveDir.setText(self.directory)
        
        notTableKeys = ["tableRows","saveDirectory"]
        col = 0
        for key in self.defaultValues.keys():
            if key not in notTableKeys:
                for row,name in enumerate(self.defaultValues[key]):
                    self.ui.diagnosticTable.setItem(row, col,QTableWidgetItem(name))
                col += 1
    
    def readTable(self):
        tableValues = {}
        for col in range(self.ui.diagnosticTable.columnCount()):
            header = self.ui.diagnosticTable.horizontalHeaderItem(col).text()
            vals = []
            for row in range(self.ui.diagnosticTable.rowCount()):
                it = self.ui.diagnosticTable.item(row, col)
                if it is not None:
                    vals.append(it.text())
                else:
                    vals.append(None)
            tableValues[header] = vals
            
        tableValues["tableRows"] = self.ui.diagnosticTable.rowCount()
        tableValues["saveDirectory"] = self.ui.saveDir.text()
    
        return tableValues
    
    def save_DefaultValues(self): 
        self.defaultValues = self.readTable()

        # Serializing json
        json_object = json.dumps(self.defaultValues, indent=4)
         
        # Writing to sample.json
        with open(self.defaultValuesPath, "w") as outfile:
            outfile.write(json_object)
    
    def add_table(self):
        row = self.ui.numberDiagnostics.value() #get value from spinbox
        rowPosition = self.ui.diagnosticTable.rowCount()
        
        if row == rowPosition+1:
            self.ui.diagnosticTable.insertRow(rowPosition) #insert new row
        elif row == rowPosition-1:
            self.ui.diagnosticTable.removeRow(row) #insert new row
        else:
            print("Undefined Change")
            
    def browseFiles(self):
        self.directory = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory",r"D:\Research\UAlberta\Research\Code\DataAcquisition"))
        self.ui.saveDir.setText(self.directory)
    
    def loadBackgroundFiles(self):
        for diagNum,diag in enumerate(self.diagInfo["Diagnostic Name"]):
            bkg_file = self.diagInfo["Background"][diagNum]
            if bkg_file != "None":
                file_Type = self.diagInfo["File Type"][diagNum]
                
                if file_Type == '.sif':
                    data, info = sif_reader.np_open(bkg_file)
                    self.backgroundData[diag] = data[0]
                else:
                    self.backgroundData[diag] = cv2.imread(bkg_file,0)
            else:
                self.backgroundData[diag] = None
    
    def confirmSetup(self):
        date = datetime.today().strftime('%Y%m%d')
        savepath = r'%s\%s_run%d\\' % (self.directory,date,self.ui.runNumber.value())
        
        self.savePlot = savepath + '\\rawplot\\'
        self.saveData = savepath + '\\data\\'
        if not os.path.exists(savepath):
            os.makedirs(savepath)
            os.makedirs(self.savePlot)
            os.makedirs(self.saveData)
            print("I have made a new folder for you which is %s"%savepath)
        
        self.diagInfo = self.readTable()
        self.loadBackgroundFiles()
        
        self.results = DAQ_Window(self)
        self.results.show()
    
    def close(self):
        #self.close()
        QtWidgets.QApplication.quit()
        sys.exit(0)  

if __name__ == "__main__":
    #app = QtWidgets.QApplication(sys.argv)
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    application = MainWindow()
    application.show()
    sys.exit(app.exec_())