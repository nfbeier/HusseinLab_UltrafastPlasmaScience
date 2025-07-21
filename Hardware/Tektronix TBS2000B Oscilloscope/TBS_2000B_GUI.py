from PyQt5 import QtWidgets, uic, QtGui, QtCore
import pyvisa
import numpy as np
import sys, threading, h5py
import json
import time, logging

from pyqtgraph import PlotWidget
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k') 

# Connect to the oscilloscope
rm = pyvisa.ResourceManager()
print(rm.list_resources())

# %%
scope = rm.open_resource('USB0::0x0699::0x03C7::C023035::INSTR')

# GUI Design file importing here (qt design file)
qtcreator_file = r"C:\Users\R2D2\Documents\CODE\Github\HusseinLab_UltrafastPlasmaScience\Hardware\Tektronix TBS2000B Oscilloscope\Ocilloscope.ui"  # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)


class WorkerThread(QtCore.QThread):
    update_signal = QtCore.pyqtSignal(np.ndarray, str, str, str, str, str, str, str, str)  # Signal includes the data and parameters

    def __init__(self, data_source, data_source2, trig_source, rec_length, v_div, v_div2, t_div, save_dir):
        super().__init__()
        self.data_source = data_source
        self.data_source2 = data_source2
        self.trig_source = trig_source
        self.rec_length = rec_length
        self.v_div = v_div
        self.v_div2 = v_div2
        self.t_div = t_div
        self.save_dir = save_dir

    def run(self):
        # Set up trigger condition
        scope.write('TRIGger:EDGE:SOURce ' + self.trig_source)   # Set the trigger source
        scope.write('TRIGger:EDGE:SLOPe POSitive')   # Set the trigger slope to positive
        scope.write('ACQuire:STATE ON')  # Turn on acquisition (ready to trigger)
        
        while True:
            # Wait for trigger event
            # scope.write('ACQuire:STATE OFF')
            try:
                scope.write('*cls') 
                scope.timeout =  60000# ms
                scope.write('ACQuire:STOPAfter SEQuence')   # Stop acquisition after one sequence
                scope.write('ACQuire:STATE ON')   # Start acquisition
                scope.query('*OPC?')  # Wait for trigger event
                # scope.write('DAT:STOP 200000')
                # scope.write('*WAI')
                # print("Triggered!")
    
                # Set up acquisition parameters
                scope.write('DATa:SOUrce ' + self.data_source)   # Select channel 4 as data source
                scope.write('DATa:ENCdg RIBinary')   # Set binary data encoding
                scope.write('WFMPre:XINcr?')   # Query the x-axis increment
                xincr = float(scope.read())   # Convert the string response to a float
                scope.write('WFMPre:YMUlt?')   # Query the y-axis scale
                yscale = float(scope.read())   # Convert the string response to a float
                scope.write('DAT:STAR 1')
                scope.write('DAT:STOP ' + self.rec_length)
                scope.write('DATa:SOUrce ' + self.data_source)
                scope.write(f'{self.data_source}:SCALE ' + self.v_div)  # Set the vertical scale of channel 4 to 1V/div
                scope.write(f'{self.data_source2}:SCALE ' + self.v_div2)  # Set the vertical scale of channel 4 to 1V/div
                scope.write('HOR:SCALE ' + self.t_div)  # Set the horizontal scale to 1ms/div
    
                # Read the acquired data
                scope.write('CURVE?')   # Query the waveform data
                data = scope.read_raw()   # Read the raw binary data
                headerlen = 2 + int(data[1])   # Determine the length of the header
                ADC_wave = data[headerlen:-1]   # Extract the ADC waveform data
                ADC_wave = np.frombuffer(ADC_wave, 'B')   # Convert the binary data to integers
                ADC_wave = ADC_wave - 127   # Convert the ADC values to signed integers
                Volts_wave = yscale * ADC_wave   # Convert the ADC values to volts
                Volts_wave = Volts_wave - np.median(Volts_wave)
                
                scope.write('DATa:SOUrce '+ self.data_source2)   # Select channel 4 as data source
                scope.write('DATa:ENCdg RIBinary')   # Set binary data encoding
                scope.write('WFMPre:XINcr?')   # Query the x-axis increment
                xincr = float(scope.read())   # Convert the string response to a float  
                scope.write('WFMPre:YMUlt?')   # Query the y-axis scale
                yscale = float(scope.read())   # Convert the string response to a float
    
                
                
                scope.write('CURVE?')   # Query the waveform data
                data = scope.read_raw()   # Read the raw binary data
                headerlen = 2 + int(data[1])   # Determine the length of the header
                header = data[:headerlen]   # Extract the header
                ADC_wave = data[headerlen:-1]   # Extract the ADC waveform data
                ADC_wave = np.frombuffer(ADC_wave, 'B')   # Convert the binary data to integers
                ADC_wave = ADC_wave - 127   # Convert the ADC values to signed integers
                Volts_wave2 = yscale * ADC_wave   # Convert the ADC values to volts
                Volts_wave2 = Volts_wave2 - np.median(Volts_wave2)
    
                # Extract the x-axis data
                xzero = float(scope.query('WFMPre:XZEro?'))
                Time_wave = np.arange(len(Volts_wave)) * xincr + xzero
    
                data_oci = np.array([Time_wave, Volts_wave, Volts_wave2])
                data_oci = data_oci.T
    
                # Emit the signal with the acquired data and parameters
                self.update_signal.emit(data_oci, self.data_source, self.data_source2, self.trig_source, self.rec_length, self.v_div, self.v_div2, self.t_div, self.save_dir)
                self.msleep(500)  # Sleep for 1 second (adjust as needed)
                
            except:
                scope.write('ACQuire:STATE OFF')
                
                # Clear existing data
                scope.write('CLEar')
                
                # Reset data source and other parameters as needed
                # ...
                
                # Restart acquisition if necessary
                scope.write('ACQuire:STATE ON')
                    


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.plot_graph.setLabel(axis='left', text='Voltage (V)')
        self.plot_graph.setLabel(axis='bottom', text='Time (s)')
        self.plot_graph.showAxis('right')
        self.plot_graph.showAxis('top')
        self.plot_graph.getAxis('top').setStyle(showValues=False)
        self.plot_graph.getAxis('right').setStyle(showValues=False)

        self.data_source_line.textChanged.connect(lambda: self.ocilloscope_inp('data_source'))
        self.data_source_line_2.textChanged.connect(lambda: self.ocilloscope_inp('data_source2'))
        self.trig_source_line.textChanged.connect(lambda: self.ocilloscope_inp('trig_source'))
        self.rec_length_line.textChanged.connect(lambda: self.ocilloscope_inp('rec_length'))
        self.v_div_line.textChanged.connect(lambda: self.ocilloscope_inp('v_div'))
        self.v_div_line_2.textChanged.connect(lambda: self.ocilloscope_inp('v_div2'))
        self.t_div_line.textChanged.connect(lambda: self.ocilloscope_inp('t_div'))
        self.SaveData_dir.textChanged.connect(lambda: self.ocilloscope_inp('save_dir'))
        self.File_num.textChanged.connect(lambda: self.ocilloscope_inp('file_num'))

        self.read_json()
        self.worker_thread = None

        self.Start.clicked.connect(self.toggle_auto_acquisition)
       
        # self.file_num
        

    def toggle_auto_acquisition(self):
        if self.worker_thread is None or not self.worker_thread.isRunning():
            self.worker_thread = WorkerThread(self.data_source, self.data_source2, self.trig_source, self.rec_length, self.v_div, self.v_div2, self.t_div, self.save_dir)
            self.worker_thread.update_signal.connect(self.update_ui)
            self.worker_thread.start()

    def update_ui(self, data_oci, data_source, data_source2, trig_source, rec_length, v_div, v_div2, t_div, save_dir):
        # Perform UI updates here
        self.plot_graph.clear()
        self.plot_graph.plot(data_oci[:, 0], data_oci[:, 1], pen='r')
        self.plot_graph.plot(data_oci[:, 0], data_oci[:, 2], pen='k')
        
        txtnum = self.file_num
        path_SaveData = save_dir
        hdf = h5py.File (path_SaveData + '/'  + time.strftime("%Y%m%d")+'_oscilloscope_data_{}.h5'.format(f"{txtnum: 05d}"), 'w')
        Ocilloscope_data = hdf.create_dataset('Oscilloscope_data', data=data_oci)
        hdf.close()
        self.Current_shot.setText('Current shot number: '+str(self.file_num))
        self.file_num += 1

    def ocilloscope_inp(self, inp):
        '''
        Checks and validates the inputs given to raster. Also clears the number of shots line
        after editing other inputs and enables/disables the raster button depending on whether
        all inputs have been entered.
        
        Parameters
        ----------
        inp (string) : LineEdit box that was edited.
        '''
        # self.messages.clear()
        
        if inp == 'data_source':
            if self.data_source_line.text():
                self.data_source = (self.data_source_line.text())
        elif inp == 'data_source2':
            if self.data_source_line_2.text():
                self.data_source2 = (self.data_source_line_2.text())
        elif inp == 'trig_source':
            if self.trig_source_line.text():
                self.trig_source = (self.trig_source_line.text())
        elif inp == 'rec_length':
            if self.rec_length_line.text():
                self.rec_length = (self.rec_length_line.text())
        elif inp == 'v_div':
            if self.v_div_line.text():
                self.v_div = (self.v_div_line.text())
        elif inp == 'v_div2':
            if self.v_div_line_2.text():
                self.v_div2 = (self.v_div_line_2.text())
        elif inp == 't_div':
            if self.t_div_line.text():
                self.t_div = (self.t_div_line.text())
        elif inp == 'save_dir':
            if self.SaveData_dir.text():
                self.save_dir = (self.SaveData_dir.text())
        elif inp == 'file_num':
            if self.File_num.text():
                self.file_num = (int(self.File_num.text()))

    def read_json(self):
        '''
        Reads the .json file and auto-fills the GUI with inputs from last use.
        '''
        with open("gui_inputs2.json", "r") as read_file:
            inputs = json.load(read_file)


        for widget in self.centralwidget.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(inputs[str(widget.objectName())])

    def write_json(self):
        '''
        Writes gui inputs to .json file to load for next use.
        '''
        with open("gui_inputs2.json", "r") as read_file:
            inputs = json.load(read_file)

        for widget in self.centralwidget.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                inputs[str(widget.objectName())] = widget.text()
    
        with open("gui_inputs2.json", "w") as write_file:
            json.dump(inputs, write_file) 

    def closeEvent(self, event):
        '''
        saves gui inputs to .json file before killing application.
        '''
        self.write_json()
        scope.close()
        rm.close()
        event.accept()
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = MyApp()
    window.show()
    app.exec_()
    # sys.exit(app.exec_())
