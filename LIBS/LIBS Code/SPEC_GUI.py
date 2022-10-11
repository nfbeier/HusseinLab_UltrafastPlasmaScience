from PyQt5 import QtWidgets, uic, QtGui, QtCore
import json

from pyqtgraph import PlotWidget
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k') 

class Spectrometers:
    def __init__(self, ui):
        self.ui = ui
        # self.read_json()
        
        self.ui.file_browse_btn.clicked.connect(self.browse_file)
        
        self.ui.plot_graph.setLabel(axis='left', text='Intensity (a.u)')
        self.ui.plot_graph.setLabel(axis='bottom', text='Wavelength (nm)')
        self.ui.plot_graph.showAxis('right')
        self.ui.plot_graph.showAxis('top')
        self.ui.plot_graph.getAxis('top').setStyle(showValues=False)
        self.ui.plot_graph.getAxis('right').setStyle(showValues=False)

        self.ui.plot_graph_2.setLabel(axis='left', text='Intensity (a.u)')
        self.ui.plot_graph_2.setLabel(axis='bottom', text='Wavelength (nm)')
        self.ui.plot_graph_2.showAxis('right')
        self.ui.plot_graph_2.showAxis('top')
        self.ui.plot_graph_2.getAxis('top').setStyle(showValues=False)
        self.ui.plot_graph_2.getAxis('right').setStyle(showValues=False)
        
        self.ui.plot_graph_3.setLabel(axis='left', text='Intensity (a.u)')
        self.ui.plot_graph_3.setLabel(axis='bottom', text='Wavelength (nm)')
        self.ui.plot_graph_3.showAxis('right')
        self.ui.plot_graph_3.showAxis('top')
        self.ui.plot_graph_3.getAxis('top').setStyle(showValues=False)
        self.ui.plot_graph_3.getAxis('right').setStyle(showValues=False)
        
        self.ui.plot_graph_4.setLabel(axis='left', text='Intensity (a.u)')
        self.ui.plot_graph_4.setLabel(axis='bottom', text='Wavelength (nm)')
        self.ui.plot_graph_4.showAxis('right')
        self.ui.plot_graph_4.showAxis('top')
        self.ui.plot_graph_4.getAxis('top').setStyle(showValues=False)
        self.ui.plot_graph_4.getAxis('right').setStyle(showValues=False)
        
        self.ui.plot_graph_5.setLabel(axis='left', text='Intensity (a.u)')
        self.ui.plot_graph_5.setLabel(axis='bottom', text='Wavelength (nm)')
        self.ui.plot_graph_5.showAxis('right')
        self.ui.plot_graph_5.showAxis('top')
        self.ui.plot_graph_5.getAxis('top').setStyle(showValues=False)
        self.ui.plot_graph_5.getAxis('right').setStyle(showValues=False)
        
        self.ui.plot_graph_6.setLabel(axis='left', text='Intensity (a.u)')
        self.ui.plot_graph_6.setLabel(axis='bottom', text='Wavelength (nm)')
        self.ui.plot_graph_6.showAxis('right')
        self.ui.plot_graph_6.showAxis('top')
        self.ui.plot_graph_6.getAxis('top').setStyle(showValues=False)
        self.ui.plot_graph_6.getAxis('right').setStyle(showValues=False)
        
    def read_json(self):
        '''
        Reads json file and auto-fills textboxes and labels on gui from last usage.
        
        Parameters
        ----------
        ui : Instance of the MyApp class from LIBSGUI.py.
        '''
        with open("gui_inputs.json", "r") as read_file:
            inputs = json.load(read_file)
          
        for widget in self.ui.spectrometers.children():
            if isinstance(widget, QtWidgets.QTextEdit):
                if widget.objectName() != "SaveData_dir":
                    widget.setText(inputs[str(widget.objectName())])

    def browse_file(self):
        '''
        Opens a file browser in directory of LIBSGUI.py file.
        '''
        # Change the 3rd parameter ("./") to change directory that browser opens in.
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self.ui,"Choose Directory","./")  
        self.ui.SaveData_dir.setText(dir_path)
        
    def set_vals(self):
        self.Laser_Energy = float(self.ui.LaserEnergy.toPlainText())
        self.Laser_Wavelength = float(self.ui.LaserWavelength.toPlainText())
        self.Laser_PulseDuration = float(self.ui.LaserPulseDuration.toPlainText())
        self.Sample_Type = self.ui.SampleType.toPlainText()
        self.Focal_Length = float(self.ui.FocalLength.toPlainText())
        self.Integration_Time = float(self.ui.IntegrationTime.toPlainText())
        self.Fiber_Angle = float(self.ui.FiberAngle.toPlainText())
        self.Background_Spectrum = self.ui.BackgroundSpectrum.toPlainText()
        self.Other_Notes = self.ui.OtherNotes.toPlainText()
        
    def clear_vals(self):
        self.ui.LaserEnergy.clear()
        self.ui.LaserWavelength.clear()
        self.ui.LaserPulseDuration.clear()
        self.ui.SampleType.clear()
        self.ui.FocalLength.clear()
        self.ui.IntegrationTime.clear()
        self.ui.FiberAngle.clear()
        self.ui.BackgroundSpectrum.clear()
        self.ui.OtherNotes.clear()
        
    def reset(self, spectrometer):
        spectrometer['device'].__del__()
        
    def write_json(self):
        '''
        Writes values from textboxes and labels on gui to json file.
        
        Parameters
        ----------
        ui : Instance of the MyApp class from LIBSGUI.py.
        '''
        with open("gui_inputs.json", "r+") as write_file:
            inputs = json.load(write_file)
    
            for widget in self.ui.spectrometers.children():
                if isinstance(widget, QtWidgets.QTextEdit) and widget.objectName() != "SaveData_dir":
                    if widget.toPlainText() != "":
                        inputs[str(widget.objectName())] = widget.toPlainText()
                    else:
                        inputs[str(widget.objectName())] = "0"
                        
            write_file.seek(0)
            json.dump(inputs, write_file)
            write_file.truncate()
