# LIBS GUI v7, 2023-11-14
# Shubho Mohajan, Ying Wan, Dr. Nicholas Beier, Dr. Amina Hussein
# University of Alberta, ECE Department

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys, threading, h5py
from fractions import Fraction
from XPS import XPS
import json
import visa

from pyqtgraph import PlotWidget
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k') 

from math import floor
# import manipulate_json


#importing resources for DG645
import instruments as ik
import quantities as pq
      

#importing resources for stellerNet
import time, logging
import numpy as np
# import the usb driver
# import stellarnet_driver3 as sn
import stellarnet_driver3 as sn
import matplotlib.pyplot as plt
logging.basicConfig(format='%(asctime)s %(message)s')

sn.installDeviceDriver()

#GUI Design file importing here (qt design file)
qtcreator_file  = "LIBS_GUI_Multiple_Spectromters_with_XPS_Oci.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

#Connecting all hardwares

# Connect Delay Generator
ins = ik.srs.SRSDG645.open_serial('COM13', 9600) # dg645

# Connect Spectrometers 
spectrometer00, wav00 = sn.array_get_spec(2) # stellerNet 400-500 nm
spectrometer11, wav11 = sn.array_get_spec(1) # stellerNet 300-400 nm
spectrometer22, wav22 = sn.array_get_spec(0) # stellerNet 190-300 nm

spectrometer33, wav33 = sn.array_get_spec(3) # stellerNet 500-600 nm
spectrometer44, wav44 = sn.array_get_spec(4) # stellerNet 600-700 nm
spectrometer55, wav55 = sn.array_get_spec(5) # stellerNet 700-800 nm

# sn.array_get_spec(#num) connect the spectrometers randomly. To ensure the wavelength range 
#here doing some conditional management

# For wav00
if 250 >= np.min(wav00) and 250 <= np.max(wav00): # to ensure spectrometer2 is 190-300 nm
    wav2 = wav00
    spectrometer2 = spectrometer00
if 350 >= np.min(wav00) and 350 <= np.max(wav00): # to ensure spectrometer1 is 300-400 nm
    wav1 = wav00
    spectrometer1 = spectrometer00
if 450 >= np.min(wav00) and 450 <= np.max(wav00): # to ensure spectrometer1 is 400-500 nm
    wav0 = wav00
    spectrometer0 = spectrometer00
if 550 >= np.min(wav00) and 550 <= np.max(wav00): # to ensure spectrometer1 is 500-600 nm
    wav3 = wav00
    spectrometer3 = spectrometer00
if 650 >= np.min(wav00) and 650 <= np.max(wav00): # to ensure spectrometer1 is 600-700 nm
    wav4 = wav00
    spectrometer4 = spectrometer00
if 750 >= np.min(wav00) and 750 <= np.max(wav00): # to ensure spectrometer1 is 500-600 nm
    wav5 = wav00
    spectrometer5 = spectrometer00

# For wav11
if 250 >= np.min(wav11) and 250 <= np.max(wav11): # to ensure spectrometer2 is 190-300 nm
    wav2 = wav11
    spectrometer2 = spectrometer11
if 350 >= np.min(wav11) and 350 <= np.max(wav11): # to ensure spectrometer1 is 300-400 nm
    wav1 = wav11
    spectrometer1 = spectrometer11
if 450 >= np.min(wav11) and 450 <= np.max(wav11): # to ensure spectrometer1 is 400-500 nm
    wav0 = wav11
    spectrometer0 = spectrometer11
if 550 >= np.min(wav11) and 550 <= np.max(wav11): # to ensure spectrometer1 is 500-600 nm
    wav3 = wav11
    spectrometer3 = spectrometer11
if 650 >= np.min(wav11) and 650 <= np.max(wav11): # to ensure spectrometer1 is 600-700 nm
    wav4 = wav11
    spectrometer4 = spectrometer11
if 750 >= np.min(wav11) and 750 <= np.max(wav11): # to ensure spectrometer1 is 500-600 nm
    wav5 = wav11
    spectrometer5 = spectrometer11
    
# For wav22
if 250 >= np.min(wav22) and 250 <= np.max(wav22): # to ensure spectrometer2 is 190-300 nm
    wav2 = wav22
    spectrometer2 = spectrometer22
if 350 >= np.min(wav22) and 350 <= np.max(wav22): # to ensure spectrometer1 is 300-400 nm
    wav1 = wav22
    spectrometer1 = spectrometer22
if 450 >= np.min(wav22) and 450 <= np.max(wav22): # to ensure spectrometer1 is 400-500 nm
    wav0 = wav22
    spectrometer0 = spectrometer22
if 550 >= np.min(wav22) and 550 <= np.max(wav22): # to ensure spectrometer1 is 500-600 nm
    wav3 = wav22
    spectrometer3 = spectrometer22
if 650 >= np.min(wav22) and 650 <= np.max(wav22): # to ensure spectrometer1 is 600-700 nm
    wav4 = wav22
    spectrometer4 = spectrometer22
if 750 >= np.min(wav22) and 750 <= np.max(wav22): # to ensure spectrometer1 is 500-600 nm
    wav5 = wav22
    spectrometer5 = spectrometer22
    
# For wav33
if 250 >= np.min(wav33) and 250 <= np.max(wav33): # to ensure spectrometer2 is 190-300 nm
    wav2 = wav33
    spectrometer2 = spectrometer33
if 350 >= np.min(wav33) and 350 <= np.max(wav33): # to ensure spectrometer1 is 300-400 nm
    wav1 = wav33
    spectrometer1 = spectrometer33
if 450 >= np.min(wav33) and 450 <= np.max(wav33): # to ensure spectrometer1 is 400-500 nm
    wav0 = wav33
    spectrometer0 = spectrometer33
if 550 >= np.min(wav33) and 550 <= np.max(wav33): # to ensure spectrometer1 is 500-600 nm
    wav3 = wav33
    spectrometer3 = spectrometer33
if 650 >= np.min(wav33) and 650 <= np.max(wav33): # to ensure spectrometer1 is 600-700 nm
    wav4 = wav33
    spectrometer4 = spectrometer33
if 750 >= np.min(wav33) and 750 <= np.max(wav33): # to ensure spectrometer1 is 500-600 nm
    wav5 = wav33
    spectrometer5 = spectrometer33
    
# For wav44
if 250 >= np.min(wav44) and 250 <= np.max(wav44): # to ensure spectrometer2 is 190-300 nm
    wav2 = wav44
    spectrometer2 = spectrometer44
if 350 >= np.min(wav44) and 350 <= np.max(wav44): # to ensure spectrometer1 is 300-400 nm
    wav1 = wav44
    spectrometer1 = spectrometer44
if 450 >= np.min(wav44) and 450 <= np.max(wav44): # to ensure spectrometer1 is 400-500 nm
    wav0 = wav44
    spectrometer0 = spectrometer44
if 550 >= np.min(wav44) and 550 <= np.max(wav44): # to ensure spectrometer1 is 500-600 nm
    wav3 = wav44
    spectrometer3 = spectrometer44
if 650 >= np.min(wav44) and 650 <= np.max(wav44): # to ensure spectrometer1 is 600-700 nm
    wav4 = wav44
    spectrometer4 = spectrometer44
if 750 >= np.min(wav44) and 750 <= np.max(wav44): # to ensure spectrometer1 is 500-600 nm
    wav5 = wav44
    spectrometer5 = spectrometer44
    
# For wav55
if 250 >= np.min(wav55) and 250 <= np.max(wav55): # to ensure spectrometer2 is 190-300 nm
    wav2 = wav55
    spectrometer2 = spectrometer55
if 350 >= np.min(wav55) and 350 <= np.max(wav55): # to ensure spectrometer1 is 300-400 nm
    wav1 = wav55
    spectrometer1 = spectrometer55
if 450 >= np.min(wav55) and 450 <= np.max(wav55): # to ensure spectrometer1 is 400-500 nm
    wav0 = wav55
    spectrometer0 = spectrometer55
if 550 >= np.min(wav55) and 550 <= np.max(wav55): # to ensure spectrometer1 is 500-600 nm
    wav3 = wav55
    spectrometer3 = spectrometer55
if 650 >= np.min(wav55) and 650 <= np.max(wav55): # to ensure spectrometer1 is 600-700 nm
    wav4 = wav55
    spectrometer4 = spectrometer55
if 750 >= np.min(wav55) and 750 <= np.max(wav55): # to ensure spectrometer1 is 500-600 nm
    wav5 = wav55
    spectrometer5 = spectrometer55
    
scansavg = 1
smooth = 1

# Connect to the oscilloscope
rm = visa.ResourceManager()
scope = rm.open_resource('USB0::0x0699::0x03C7::C020817::INSTR')

#Global variables for data saving and plotting
data_stellar0 = None # wavelength and intensity for stellerNet
data_stellar1 = None
data_stellar2 = None
data_stellar3 = None
data_stellar4 = None
data_stellar5 = None

data_oci = None

intensity_steller0_all = np.zeros((2048, 2)) # for storing previous shot stellernet intensity
intensity_steller1_all = np.zeros((2048, 2))
intensity_steller2_all = np.zeros((2048, 2))
intensity_steller3_all = np.zeros((2048, 2))
intensity_steller4_all = np.zeros((2048, 2))
intensity_steller5_all = np.zeros((2048, 2))

data_stellar0_bkg = np.zeros((2048, 1))
data_stellar1_bkg = np.zeros((2048, 1))
data_stellar2_bkg = np.zeros((2048, 1))
data_stellar3_bkg = np.zeros((2048, 1))
data_stellar4_bkg = np.zeros((2048, 1))
data_stellar5_bkg = np.zeros((2048, 1))



class StellerNet_functions:
    
    #function for getting spectrum f rom stellArNet
    def getSpectrum(spectrometer, wav, inttime, scansavg, smooth):
        logging.warning('requesting spectrum')
        spectrometer['device'].set_config(int_time=inttime, scans_to_avg=scansavg, x_smooth=smooth)
        sn.setTempComp(spectrometer, True) 
        spectrum = sn.array_spectrum(spectrometer, wav)
        logging.warning('recieved spectrum')
        return spectrum 
    
    # function external triger of stellarNet    
    def external_trigger(spectrometer,trigger):
        sn.ext_trig(spectrometer,trigger)    


class StellerNet0TriggerThread(threading.Thread):
    def __init__(self, inttime):
        super(StellerNet0TriggerThread,self).__init__()
        self.inttime = inttime
        global data_stellar0
        logging.warning('displaying spectrum')
        StellerNet_functions.external_trigger(spectrometer0,True)
        data_stellar0 = StellerNet_functions.getSpectrum(spectrometer0, wav0, inttime, scansavg, smooth)


class StellerNet1TriggerThread(threading.Thread):
    def __init__(self, inttime):
        super(StellerNet1TriggerThread,self).__init__()
        self.inttime = inttime
        global data_stellar1
        logging.warning('displaying spectrum')
        StellerNet_functions.external_trigger(spectrometer1,True)
        data_stellar1 = StellerNet_functions.getSpectrum(spectrometer1, wav1, inttime, scansavg, smooth)


class StellerNet2TriggerThread(threading.Thread):
    def __init__(self, inttime):
        super(StellerNet2TriggerThread,self).__init__()
        self.inttime = inttime
        global data_stellar2
        logging.warning('displaying spectrum')
        StellerNet_functions.external_trigger(spectrometer2,True)
        data_stellar2 = StellerNet_functions.getSpectrum(spectrometer2, wav2, inttime, scansavg, smooth)

class StellerNet3TriggerThread(threading.Thread):
    def __init__(self, inttime):
        super(StellerNet3TriggerThread,self).__init__()
        self.inttime = inttime
        global data_stellar3
        logging.warning('displaying spectrum')
        StellerNet_functions.external_trigger(spectrometer3,True)
        data_stellar3 = StellerNet_functions.getSpectrum(spectrometer3, wav3, inttime, scansavg, smooth)

class StellerNet4TriggerThread(threading.Thread):
    def __init__(self, inttime):
        super(StellerNet4TriggerThread,self).__init__()
        self.inttime = inttime
        global data_stellar4
        logging.warning('displaying spectrum')
        StellerNet_functions.external_trigger(spectrometer4,True)
        data_stellar4 = StellerNet_functions.getSpectrum(spectrometer4, wav4, inttime, scansavg, smooth)

class StellerNet5TriggerThread(threading.Thread):
    def __init__(self, inttime):
        super(StellerNet5TriggerThread,self).__init__()
        self.inttime = inttime
        global data_stellar5
        logging.warning('displaying spectrum')
        StellerNet_functions.external_trigger(spectrometer5,True)
        data_stellar5 = StellerNet_functions.getSpectrum(spectrometer5, wav5, inttime, scansavg, smooth)
        
class ocilloscopeThread(threading.Thread):
    def __init__(self, data_source, trig_source, v_div, t_div, rec_length):
        super(ocilloscopeThread,self).__init__()
        # self.start = start
        global data_oci
        data_oci=self.ocilloscope(data_source, trig_source, v_div, t_div, rec_length)
    def ocilloscope(self, data_source, trig_source, v_div, t_div, rec_length):
        # Set up acquisition parameters
        scope.write('DATa:SOUrce '+ data_source)   # Select channel 4 as data source
        scope.write('DATa:ENCdg RIBinary')   # Set binary data encoding
        scope.write('WFMPre:XINcr?')   # Query the x-axis increment
        xincr = float(scope.read())   # Convert the string response to a float  
        scope.write('WFMPre:YMUlt?')   # Query the y-axis scale
        yscale = float(scope.read())   # Convert the string response to a float
        scope.write('TRIGger:EDGE:SOURce '+ trig_source)   # Set the trigger source to channel 4
        scope.write('TRIGger:EDGE:SLOPe POSitive')   # Set the trigger slope to positive
        # scope.write('TRIGger:LEVel CH1,0')   # Set the trigger level to 0V
        scope.write('DAT:STAR 1')
        scope.write('DAT:STOP '+ rec_length)
        scope.write('DAT:STOP '+ data_source)
        scope.write('CH1:SCALE '+ v_div)  # Set the vertical scale of channel 4 to 1V/div
        scope.write('HOR:SCALE '+ t_div) # Set the horizontal scale to 1ms/div
        
        # Arm the scope and wait for trigger
        scope.write('ACQuire:STOPAfter SEQuence')   # Stop acquisition after one sequence
        scope.write('ACQuire:STATE ON')   # Start acquisition
        scope.query('*OPC?')   # Wait for acquisition to complete

        # Read the acquired data
        scope.write('CURVE?')   # Query the waveform data
        data = scope.read_raw()   # Read the raw binary data
        headerlen = 2 + int(data[1])   # Determine the length of the header
        header = data[:headerlen]   # Extract the header
        ADC_wave = data[headerlen:-1]   # Extract the ADC waveform data
        ADC_wave = np.frombuffer(ADC_wave, 'B')   # Convert the binary data to integers
        ADC_wave = ADC_wave - 127   # Convert the ADC values to signed integers
        Volts_wave = yscale * ADC_wave   # Convert the ADC values to volts
        Volts_wave = Volts_wave - np.mean(Volts_wave)
        
        # Extract the x-axis data
        xzero = float(scope.query('WFMPre:XZEro?'))
        Time_wave = np.arange(len(Volts_wave)) * xincr + xzero
        
        # Time_wave = np.arange(0, xincr * len(Volts_wave), xincr)   # Generate the time axis
        # Time_wave = np.linspace(0, xincr * len(Volts_wave), len(Volts_wave))   # Generate the time axis
        data_oci = np.array([Time_wave, Volts_wave])
        data_oci = data_oci.T
        
        return data_oci
        
        # self.plot_graph_10.clear()
        # self.plot_graph_10.plot(Time_wave, Volts_wave, pen='r')


class FireThread(threading.Thread):
    def __init__(self, clicked):
        super(FireThread, self).__init__()
        self.clicked = clicked
        ins.sendcmd('TSRC 5') 
        ins.sendcmd('*TRG')


# Main class for GUI
class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)


        
        # STAGE CONTROL ----------------------------------------------------------------------        
        # self.setupUi(self)
        self.x_xps = XPS()
        self.y_xps = XPS()
        
        self.abs_min = [0, 0]
        self.abs_max = [50, 50]

        # X-Axis Combo Box
        self.xps_groups = self.x_xps.getXPSStatus()
        self.x_group_combo.clear()
        self.x_group_combo.addItems(list(self.xps_groups.keys()))
        self.x_axis = str(self.x_group_combo.currentText())
        self.x_xps.setGroup(self.x_axis)
        self.stageStatus = self.x_xps.getStageStatus(self.x_axis)
        self.update_group("X")
        self.x_group_combo.activated.connect(lambda: self.update_group("X"))

        # Y-Axis Combo Box
        self.y_group_combo.clear()
        self.y_group_combo.addItems(list(self.xps_groups.keys()))
        self.y_group_combo.setCurrentIndex(1)
        self.y_axis = str(self.y_group_combo.currentText())
        self.y_xps.setGroup(self.y_axis)
        self.stageStatus = self.y_xps.getStageStatus(self.y_axis)
        self.update_group("Y")
        self.y_group_combo.activated.connect(lambda: self.update_group("Y"))
        
        # Status Buttons
        self.initialize_btn.clicked.connect(self.initialize)
        self.kill_btn.clicked.connect(self.kill)
        self.enable_btn.clicked.connect(self.enable_disable)
        
        # Travel Limits
        self.x_min_line.textChanged.connect(lambda: self.set_minmax("x", "min", self.x_min_line.text()))
        self.x_max_line.textChanged.connect(lambda: self.set_minmax("x", "max", self.x_max_line.text()))
        self.y_min_line.textChanged.connect(lambda: self.set_minmax("y", "min", self.y_min_line.text()))
        self.y_max_line.textChanged.connect(lambda: self.set_minmax("y", "max", self.y_max_line.text()))
        
        # Relative Motion Controls
        self.rel_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.left_btn.clicked.connect(lambda: self.relative('left'))
        self.right_btn.clicked.connect(lambda: self.relative('right'))
        self.down_btn.clicked.connect(lambda: self.relative('down'))
        self.up_btn.clicked.connect(lambda: self.relative('up'))

        # Absolute Motion Controls
        self.abs_x_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.abs_y_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.abs_move_btn.clicked.connect(self.absolute)

        # Reference Point Commands
        self.ref = [0, 0]
        self.set_btn.clicked.connect(lambda: self.ref_commands('set'))
        self.return_btn.clicked.connect(lambda: self.ref_commands('return'))
        
        # Raster Input Boxes
        self.step_length_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.step_length_line.textChanged.connect(lambda: self.raster_inp('step_length'))
        self.sample_length_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.sample_length_line.textChanged.connect(lambda: self.raster_inp('sample_length'))
        self.sample_width_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.sample_width_line.textChanged.connect(lambda: self.raster_inp('sample_width'))
        self.set_x_btn.clicked.connect(lambda: self.raster_inp('set_bound_x'))
        self.set_y_btn.clicked.connect(lambda: self.raster_inp('set_bound_y'))
        self.num_shots_line.setEnabled(False)
        self.num_shots_line.textChanged.connect(lambda: self.raster_inp('num_shots'))
        
        # Raster Controls
        self.raster_btn.setEnabled(False)
        self.raster_btn.clicked.connect(self.start_timer)
        self.stop_btn_2.clicked.connect(self.end_timer)
        
        # Timer and Printing of Stage Location
        self.print_timer = QtCore.QTimer(self, interval = 1000, timeout = self.print_location)
        self.print_timer.start()
        self.print_location()
        
         
        # -------------------------------------------------------------------------------------
        
# Ocilloscope ----------------------------------------------------------------------   

        # self.data_source_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.data_source_line.textChanged.connect(lambda: self.ocilloscope_inp('data_source'))
        # self.trig_source_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.trig_source_line.textChanged.connect(lambda: self.ocilloscope_inp('trig_source'))
        self.rec_length_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.rec_length_line.textChanged.connect(lambda: self.ocilloscope_inp('rec_length'))
        self.v_div_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.v_div_line.textChanged.connect(lambda: self.ocilloscope_inp('v_div'))
        self.t_div_line.setValidator(QtGui.QDoubleValidator(0.10, 50.00, 2))
        self.t_div_line.textChanged.connect(lambda: self.ocilloscope_inp('t_div'))
        
        # self.Time_data = 0
        # self.Volts_data=0



#-------------------------------------------------------------------------------------   
    

        self.set_param_dg_A.clicked.connect(self.DGParamA)
        self.set_param_dg_B.clicked.connect(self.DGParamB)
        self.set_param_dg_C.clicked.connect(self.DGParamC)
        self.set_param_dg_D.clicked.connect(self.DGParamD)
        self.set_param_dg_E.clicked.connect(self.DGParamE)
        self.set_param_dg_F.clicked.connect(self.DGParamF)
        self.set_param_dg_G.clicked.connect(self.DGParamG)
        self.set_param_dg_H.clicked.connect(self.DGParamH)
        self.set_param_dg_AB.clicked.connect(self.DGParamAB)
        self.set_param_dg_CD.clicked.connect(self.DGParamCD)
        self.set_param_dg_EF.clicked.connect(self.DGParamEF)
        self.set_param_dg_GH.clicked.connect(self.DGParamGH)
        self.set_exp_param.clicked.connect(self.MetaData)
        self.T0_disp.clicked.connect(self.T0_click)
        self.T1_disp.clicked.connect(self.T1_click)
        self.A_disp.clicked.connect(self.A_click)
        self.B_disp.clicked.connect(self.B_click)
        self.C_disp.clicked.connect(self.C_click)
        self.D_disp.clicked.connect(self.D_click)
        self.E_disp.clicked.connect(self.E_click)
        self.F_disp.clicked.connect(self.F_click)
        self.G_disp.clicked.connect(self.G_click)
        self.H_disp.clicked.connect(self.H_click)
        
        self.file_browse_btn.clicked.connect(self.browse_file)
        # self.Start.clicked.connect(self.start_raster)
        self.disconnect_all.clicked.connect(self.DisconnectAll)

        self.plot_graph_7.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_7.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_7.showAxis('right')
        self.plot_graph_7.showAxis('top')
        self.plot_graph_7.getAxis('top').setStyle(showValues=False)
        self.plot_graph_7.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_8.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_8.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_8.showAxis('right')
        self.plot_graph_8.showAxis('top')
        self.plot_graph_8.getAxis('top').setStyle(showValues=False)
        self.plot_graph_8.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_9.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_9.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_9.showAxis('right')
        self.plot_graph_9.showAxis('top')
        self.plot_graph_9.getAxis('top').setStyle(showValues=False)
        self.plot_graph_9.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_10.setLabel(axis='left', text='Voltage (V)')
        self.plot_graph_10.setLabel(axis='bottom', text='Time (s)')
        self.plot_graph_10.showAxis('right')
        self.plot_graph_10.showAxis('top')
        self.plot_graph_10.getAxis('top').setStyle(showValues=False)
        self.plot_graph_10.getAxis('right').setStyle(showValues=False)

        
        self.read_json()
        self.MetaData()
        
        self.file_num = 1
        self.same_loc_shot = 1
        self.num_shots_same_loc = int(self.num_shots_same_loc_txt.text())
        self.num_shots_same_loc_txt.textEdited.connect(lambda: self.raster_inp("shots_same_loc"))

    def read_json(self):
        '''
        Reads the .json file and auto-fills the GUI with inputs from last use.
        '''
        with open("gui_inputs2.json", "r") as read_file:
            inputs = json.load(read_file)

        for widget in self.spectrometers.children():
            if isinstance(widget, QtWidgets.QTextEdit):
                widget.setText(inputs[str(widget.objectName())])

        for widget in self.dg.children():
            if isinstance(widget, QtWidgets.QTextEdit):
                widget.setText(inputs[str(widget.objectName())])
            
        for widget in self.translationStage.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(inputs[str(widget.objectName())])

        for widget in self.Ocilloscope.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(inputs[str(widget.objectName())])


    # def write_json(self):
    #     '''
    #     Writes gui inputs to .json file to load for next use.
    #     '''
    #     with open("gui_inputs2.json", "r+") as write_file:
    #         inputs = json.load(write_file)

    #         for widget in self.spectrometers.children():
    #             if isinstance(widget, QtWidgets.QTextEdit):
    #                 inputs[str(widget.objectName())] = widget.toPlainText()
                    
    #         for widget in self.dg.children():
    #             if isinstance(widget, QtWidgets.QTextEdit):
    #                 inputs[str(widget.objectName())] = widget.toPlainText()
            
    #         for widget in self.translationStage.children():
    #             if isinstance(widget, QtWidgets.QLineEdit):
    #                 inputs[str(widget.objectName())] = widget.text()

    #         for widget in self.Ocilloscope.children():
    #             if isinstance(widget, QtWidgets.QLineEdit):
    #                 inputs[str(widget.objectName())] = widget.text()
                
    #         write_file.seek(0)
    #         json.dump(inputs, write_file)
    #         write_file.truncate

    def write_json(self):
        '''
        Writes gui inputs to .json file to load for next use.
        '''
        with open("gui_inputs2.json", "r") as read_file:
            inputs = json.load(read_file)
    
        for widget in self.spectrometers.children():
            if isinstance(widget, QtWidgets.QTextEdit):
                inputs[str(widget.objectName())] = widget.toPlainText()
                    
        for widget in self.dg.children():
            if isinstance(widget, QtWidgets.QTextEdit):
                inputs[str(widget.objectName())] = widget.toPlainText()
                
        for widget in self.translationStage.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                inputs[str(widget.objectName())] = widget.text()

        for widget in self.Ocilloscope.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                inputs[str(widget.objectName())] = widget.text()
    
        with open("gui_inputs2.json", "w") as write_file:
            json.dump(inputs, write_file) 
            
    def MetaData(self):
        self.Laser_Energy = float(self.LaserEnergy.toPlainText())
        self.Laser_Wavelength = float(self.LaserWavelength.toPlainText())
        self.Laser_PulseDuration = float(self.LaserPulseDuration.toPlainText())
        self.Sample_Type = self.SampleType.toPlainText()
        self.Focal_Length = float(self.FocalLength.toPlainText())
        self.Integration_Time = float(self.IntegrationTime.toPlainText())
        self.Fiber_Angle = float(self.FiberAngle.toPlainText())
        self.Background_Spectrum = self.BackgroundSpectrum.toPlainText()
        self.Other_Notes = self.OtherNotes.toPlainText()
        
    def DGParamA(self):
        ins.channel["A"].delay = (ins.channel[self.A_ch.toPlainText()], pq.Quantity(float(self.A_delay.toPlainText()), self.A_delay_unit.toPlainText()))
    def DGParamB(self):
        ins.channel["B"].delay = (ins.channel[self.B_ch.toPlainText()], pq.Quantity(float(self.B_delay.toPlainText()), self.B_delay_unit.toPlainText()))
    def DGParamC(self):
        ins.channel["C"].delay = (ins.channel[self.C_ch.toPlainText()], pq.Quantity(float(self.C_delay.toPlainText()), self.C_delay_unit.toPlainText()))
    def DGParamD(self):
         ins.channel["D"].delay = (ins.channel[self.D_ch.toPlainText()], pq.Quantity(float(self.D_delay.toPlainText()), self.D_delay_unit.toPlainText()))
    def DGParamE(self):
        ins.channel["E"].delay = (ins.channel[self.E_ch.toPlainText()], pq.Quantity(float(self.E_delay.toPlainText()), self.E_delay_unit.toPlainText()))
    def DGParamF(self):
        ins.channel["F"].delay = (ins.channel[self.F_ch.toPlainText()], pq.Quantity(float(self.F_delay.toPlainText()), self.F_delay_unit.toPlainText()))
    def DGParamG(self):
        ins.channel["G"].delay = (ins.channel[self.G_ch.toPlainText()], pq.Quantity(float(self.G_delay.toPlainText()), self.G_delay_unit.toPlainText()))
    def DGParamH(self):
         ins.channel["H"].delay = (ins.channel[self.H_ch.toPlainText()], pq.Quantity(float(self.H_delay.toPlainText()), self.H_delay_unit.toPlainText()))
    def DGParamAB(self):
        ins.output["AB"].level_offset = pq.Quantity(float(self.AB_offset.toPlainText()), "V")
        ins.output["AB"].level_amplitude = pq.Quantity(float(self.AB_Amp.toPlainText()), "V")
    def DGParamCD(self):
        ins.output["CD"].level_offset = pq.Quantity(float(self.CD_offset.toPlainText()), "V")
        ins.output["CD"].level_amplitude = pq.Quantity(float(self.CD_Amp.toPlainText()), "V")
    def DGParamEF(self):
        ins.output["EF"].level_offset = pq.Quantity(float(self.EF_offset.toPlainText()), "V")
        ins.output["EF"].level_amplitude = pq.Quantity(float(self.EF_Amp.toPlainText()), "V")
    def DGParamGH(self):
         ins.output["GH"].level_offset = pq.Quantity(float(self.GH_offset.toPlainText()), "V")
         ins.output["GH"].level_amplitude = pq.Quantity(float(self.GH_Amp.toPlainText()), "V")
    
    def T0_click(self):
        ins.sendcmd('DISP 11,0')
    def T1_click(self):
        ins.sendcmd('DISP 11,1')
    def A_click(self):
        ins.sendcmd('DISP 11,2')
    def B_click(self):
        ins.sendcmd('DISP 11,3')
    def C_click(self):
        ins.sendcmd('DISP 11,4')
    def D_click(self):
        ins.sendcmd('DISP 11,5')
    def E_click(self):
        ins.sendcmd('DISP 11,6')
    def F_click(self):
        ins.sendcmd('DISP 11,7')
    def G_click(self):
        ins.sendcmd('DISP 11,8')
    def H_click(self):
        ins.sendcmd('DISP 11,9')

    def browse_file(self):
        '''
        Opens a file browser in directory of LIBSGUI.py file.
        '''
        dir_path=QtWidgets.QFileDialog.getExistingDirectory(self,"Choose Directory","./")  # Change the 3rd parameter ("./") to change directory that browser opens in.
        self.SaveData_dir.setText(dir_path)
        
    def MySpectrometers(self):
        # Calling hardware threads   
        StellerNet0TrigThread = threading.Thread(target=StellerNet0TriggerThread, args=(self.inttime, ))
        StellerNet1TrigThread = threading.Thread(target=StellerNet1TriggerThread, args=(self.inttime, ))
        StellerNet2TrigThread = threading.Thread(target=StellerNet2TriggerThread, args=(self.inttime, ))
        StellerNet3TrigThread = threading.Thread(target=StellerNet3TriggerThread, args=(self.inttime, ))
        StellerNet4TrigThread = threading.Thread(target=StellerNet4TriggerThread, args=(self.inttime, ))
        StellerNet5TrigThread = threading.Thread(target=StellerNet5TriggerThread, args=(self.inttime, ))
        ocilloscopeTrigThread = threading.Thread(target=ocilloscopeThread, args=(self.data_source,self.trig_source,self.v_div, self.t_div, self.rec_length))
        Fire = threading.Thread(target=FireThread, args=(10, ))

        # Start Parallel Operation of hardwares
        # ThorlabsTrigThread.start()
        StellerNet0TrigThread.start()
        StellerNet1TrigThread.start()
        StellerNet2TrigThread.start()
        StellerNet3TrigThread.start()
        StellerNet4TrigThread.start()
        StellerNet5TrigThread.start()
        ocilloscopeTrigThread.start()
        time.sleep(1)
        Fire.start()
        # data_oci = np.array(self.Time_data, self.Volts_data)
        
        # ThorlabsTrigThread.join()
        StellerNet0TrigThread.join()
        StellerNet1TrigThread.join()
        StellerNet2TrigThread.join()
        StellerNet3TrigThread.join()
        StellerNet4TrigThread.join()
        StellerNet5TrigThread.join()
        ocilloscopeTrigThread.join()
        Fire.join()     

        
        # calling variables for sending data from thread
        # global data_thor
        global data_stellar0
        global data_stellar1
        global data_stellar2
        global data_stellar3
        global data_stellar4
        global data_stellar5        
        global data_oci

        global intensity_steller0_all
        global intensity_steller1_all
        global intensity_steller2_all
        global intensity_steller3_all
        global intensity_steller4_all
        global intensity_steller5_all
        
        global data_stellar0_bkg
        global data_stellar1_bkg
        global data_stellar2_bkg
        global data_stellar3_bkg
        global data_stellar4_bkg
        global data_stellar5_bkg
        

        temp_steller0 = data_stellar0[:,1].reshape(2048,1)
        intensity_steller0_all = np.hstack([intensity_steller0_all, temp_steller0])
        temp_steller1 = data_stellar1[:,1].reshape(2048,1)
        intensity_steller1_all = np.hstack([intensity_steller1_all, temp_steller1])
        temp_steller2 = data_stellar2[:,1].reshape(2048,1)
        intensity_steller2_all = np.hstack([intensity_steller2_all, temp_steller2])
        temp_steller3 = data_stellar3[:,1].reshape(2048,1)
        intensity_steller3_all = np.hstack([intensity_steller3_all, temp_steller3])
        temp_steller4 = data_stellar4[:,1].reshape(2048,1)
        intensity_steller4_all = np.hstack([intensity_steller4_all, temp_steller4])
        temp_steller5 = data_stellar5[:,1].reshape(2048,1)
        intensity_steller5_all = np.hstack([intensity_steller5_all, temp_steller5])
        
        #plotting
        if self.acquire_bkg.isChecked():
            data_stellar0_bkg = np.hstack([data_stellar0_bkg, data_stellar0[:,1].reshape(2048,1)])
            data_stellar1_bkg = np.hstack([data_stellar1_bkg, data_stellar1[:,1].reshape(2048,1)])
            data_stellar2_bkg = np.hstack([data_stellar2_bkg, data_stellar2[:,1].reshape(2048,1)])
            data_stellar3_bkg = np.hstack([data_stellar3_bkg, data_stellar3[:,1].reshape(2048,1)])
            data_stellar4_bkg = np.hstack([data_stellar4_bkg, data_stellar4[:,1].reshape(2048,1)])
            data_stellar5_bkg = np.hstack([data_stellar5_bkg, data_stellar5[:,1].reshape(2048,1)])

        else:
            avg_data_stellar0_bkg = np.mean(data_stellar0_bkg, axis=1).reshape(2048,1)
            avg_data_stellar1_bkg = np.mean(data_stellar1_bkg, axis=1).reshape(2048,1)
            avg_data_stellar2_bkg = np.mean(data_stellar2_bkg, axis=1).reshape(2048,1)
            avg_data_stellar3_bkg = np.mean(data_stellar3_bkg, axis=1).reshape(2048,1)
            avg_data_stellar4_bkg = np.mean(data_stellar4_bkg, axis=1).reshape(2048,1)
            avg_data_stellar5_bkg = np.mean(data_stellar5_bkg, axis=1).reshape(2048,1)
            

        if self.subtract_bkg.isChecked():
            if self.acquire_bkg.isChecked():
                self.plot_graph_7.clear()
                self.plot_graph_7.plot(data_stellar0[:,0],intensity_steller0_all[:,-1], pen='y')
                self.plot_graph_7.plot(data_stellar1[:,0],intensity_steller1_all[:,-1], pen='c')
                self.plot_graph_7.plot(data_stellar2[:,0],intensity_steller2_all[:,-1], pen='b')
                self.plot_graph_7.plot(data_stellar3[:,0],intensity_steller3_all[:,-1], pen='g')
                self.plot_graph_7.plot(data_stellar4[:,0],intensity_steller4_all[:,-1], pen='m')
                self.plot_graph_7.plot(data_stellar5[:,0],intensity_steller5_all[:,-1], pen='r')
        
                self.plot_graph_8.clear()
                self.plot_graph_8.plot(data_stellar0[:,0],intensity_steller0_all[:,-2], pen='y')
                self.plot_graph_8.plot(data_stellar1[:,0],intensity_steller1_all[:,-2], pen='c')
                self.plot_graph_8.plot(data_stellar2[:,0],intensity_steller2_all[:,-2], pen='b')
                self.plot_graph_8.plot(data_stellar3[:,0],intensity_steller3_all[:,-2], pen='g')
                self.plot_graph_8.plot(data_stellar4[:,0],intensity_steller4_all[:,-2], pen='m')
                self.plot_graph_8.plot(data_stellar5[:,0],intensity_steller5_all[:,-2], pen='r')
        
                self.plot_graph_9.clear()
                self.plot_graph_9.plot(data_stellar0[:,0],intensity_steller0_all[:,-3], pen='y')
                self.plot_graph_9.plot(data_stellar1[:,0],intensity_steller1_all[:,-3], pen='c')
                self.plot_graph_9.plot(data_stellar2[:,0],intensity_steller2_all[:,-3], pen='b')
                self.plot_graph_9.plot(data_stellar3[:,0],intensity_steller3_all[:,-3], pen='g')
                self.plot_graph_9.plot(data_stellar4[:,0],intensity_steller4_all[:,-3], pen='m')
                self.plot_graph_9.plot(data_stellar5[:,0],intensity_steller5_all[:,-3], pen='r')
            else:
                self.plot_graph_7.clear()
                self.plot_graph_7.plot(data_stellar0[:,0].reshape(2048,),(intensity_steller0_all[:,-1].reshape(2048,)-avg_data_stellar0_bkg.reshape(2048,)), pen='y')
                self.plot_graph_7.plot(data_stellar1[:,0].reshape(2048,),(intensity_steller1_all[:,-1].reshape(2048,)-avg_data_stellar1_bkg.reshape(2048,)), pen='c')
                self.plot_graph_7.plot(data_stellar2[:,0].reshape(2048,),(intensity_steller2_all[:,-1].reshape(2048,)-avg_data_stellar2_bkg.reshape(2048,)), pen='b')
                self.plot_graph_7.plot(data_stellar3[:,0].reshape(2048,),(intensity_steller3_all[:,-1].reshape(2048,)-avg_data_stellar3_bkg.reshape(2048,)), pen='g')
                self.plot_graph_7.plot(data_stellar4[:,0].reshape(2048,),(intensity_steller4_all[:,-1].reshape(2048,)-avg_data_stellar4_bkg.reshape(2048,)), pen='m')
                self.plot_graph_7.plot(data_stellar5[:,0].reshape(2048,),(intensity_steller5_all[:,-1].reshape(2048,)-avg_data_stellar5_bkg.reshape(2048,)), pen='r')
    
                self.plot_graph_8.clear()
                self.plot_graph_8.plot(data_stellar0[:,0].reshape(2048,),(intensity_steller0_all[:,-2].reshape(2048,)-avg_data_stellar0_bkg.reshape(2048,)), pen='y')
                self.plot_graph_8.plot(data_stellar1[:,0].reshape(2048,),(intensity_steller1_all[:,-2].reshape(2048,)-avg_data_stellar1_bkg.reshape(2048,)), pen='c')
                self.plot_graph_8.plot(data_stellar2[:,0].reshape(2048,),(intensity_steller2_all[:,-2].reshape(2048,)-avg_data_stellar2_bkg.reshape(2048,)), pen='b')
                self.plot_graph_8.plot(data_stellar3[:,0].reshape(2048,),(intensity_steller3_all[:,-2].reshape(2048,)-avg_data_stellar3_bkg.reshape(2048,)), pen='g')
                self.plot_graph_8.plot(data_stellar4[:,0].reshape(2048,),(intensity_steller4_all[:,-2].reshape(2048,)-avg_data_stellar4_bkg.reshape(2048,)), pen='m')
                self.plot_graph_8.plot(data_stellar5[:,0].reshape(2048,),(intensity_steller5_all[:,-2].reshape(2048,)-avg_data_stellar5_bkg.reshape(2048,)), pen='r')
    
                self.plot_graph_9.clear()
                self.plot_graph_9.plot(data_stellar0[:,0].reshape(2048,),(intensity_steller0_all[:,-3].reshape(2048,)-avg_data_stellar0_bkg.reshape(2048,)), pen='y')
                self.plot_graph_9.plot(data_stellar1[:,0].reshape(2048,),(intensity_steller1_all[:,-3].reshape(2048,)-avg_data_stellar1_bkg.reshape(2048,)), pen='c')
                self.plot_graph_9.plot(data_stellar2[:,0].reshape(2048,),(intensity_steller2_all[:,-3].reshape(2048,)-avg_data_stellar2_bkg.reshape(2048,)), pen='b')
                self.plot_graph_9.plot(data_stellar3[:,0].reshape(2048,),(intensity_steller3_all[:,-3].reshape(2048,)-avg_data_stellar3_bkg.reshape(2048,)), pen='g')
                self.plot_graph_9.plot(data_stellar4[:,0].reshape(2048,),(intensity_steller4_all[:,-3].reshape(2048,)-avg_data_stellar4_bkg.reshape(2048,)), pen='m')
                self.plot_graph_9.plot(data_stellar5[:,0].reshape(2048,),(intensity_steller5_all[:,-3].reshape(2048,)-avg_data_stellar5_bkg.reshape(2048,)), pen='r')
            
        else:
            self.plot_graph_7.clear()
            self.plot_graph_7.plot(data_stellar0[:,0],intensity_steller0_all[:,-1], pen='y')
            self.plot_graph_7.plot(data_stellar1[:,0],intensity_steller1_all[:,-1], pen='c')
            self.plot_graph_7.plot(data_stellar2[:,0],intensity_steller2_all[:,-1], pen='b')
            self.plot_graph_7.plot(data_stellar3[:,0],intensity_steller3_all[:,-1], pen='g')
            self.plot_graph_7.plot(data_stellar4[:,0],intensity_steller4_all[:,-1], pen='m')
            self.plot_graph_7.plot(data_stellar5[:,0],intensity_steller5_all[:,-1], pen='r')
    
            self.plot_graph_8.clear()
            self.plot_graph_8.plot(data_stellar0[:,0],intensity_steller0_all[:,-2], pen='y')
            self.plot_graph_8.plot(data_stellar1[:,0],intensity_steller1_all[:,-2], pen='c')
            self.plot_graph_8.plot(data_stellar2[:,0],intensity_steller2_all[:,-2], pen='b')
            self.plot_graph_8.plot(data_stellar3[:,0],intensity_steller3_all[:,-2], pen='g')
            self.plot_graph_8.plot(data_stellar4[:,0],intensity_steller4_all[:,-2], pen='m')
            self.plot_graph_8.plot(data_stellar5[:,0],intensity_steller5_all[:,-2], pen='r')
    
            self.plot_graph_9.clear()
            self.plot_graph_9.plot(data_stellar0[:,0],intensity_steller0_all[:,-3], pen='y')
            self.plot_graph_9.plot(data_stellar1[:,0],intensity_steller1_all[:,-3], pen='c')
            self.plot_graph_9.plot(data_stellar2[:,0],intensity_steller2_all[:,-3], pen='b')
            self.plot_graph_9.plot(data_stellar3[:,0],intensity_steller3_all[:,-3], pen='g')
            self.plot_graph_9.plot(data_stellar4[:,0],intensity_steller4_all[:,-3], pen='m')
            self.plot_graph_9.plot(data_stellar5[:,0],intensity_steller5_all[:,-3], pen='r')
        
        # Deleting 4th shot data for memory efficiency
        intensity_steller0_all = np.delete(intensity_steller0_all, 0, 1)
        intensity_steller1_all = np.delete(intensity_steller1_all, 0, 1)
        intensity_steller2_all = np.delete(intensity_steller2_all, 0, 1)
        intensity_steller3_all = np.delete(intensity_steller3_all, 0, 1)
        intensity_steller4_all = np.delete(intensity_steller4_all, 0, 1)
        intensity_steller5_all = np.delete(intensity_steller5_all, 0, 1)
        
        self.plot_graph_10.clear()
        self.plot_graph_10.plot(data_oci[:,0], data_oci[:,1], pen='r')
        
        #Save Data
        txtnum = self.file_num
        path_SaveData = self.SaveData_dir.toPlainText()
        hdf = h5py.File (path_SaveData + '/'  + time.strftime("%Y%m%d")+'_LIBS_Spectrum_{}.h5'.format(txtnum), 'w')
        StellarNetSpectrum_400_500nm = hdf.create_dataset('StellarNetSpectrum_400_500nm', data=data_stellar0)
        StellarNetSpectrum_300_400nm = hdf.create_dataset('StellarNetSpectrum_300_400nm', data=data_stellar1)
        StellarNetSpectrum_190_300nm = hdf.create_dataset('StellarNetSpectrum_190_300nm', data=data_stellar2)
        StellarNetSpectrum_500_600nm = hdf.create_dataset('StellarNetSpectrum_500_600nm', data=data_stellar3)
        StellarNetSpectrum_600_700nm = hdf.create_dataset('StellarNetSpectrum_600_700nm', data=data_stellar4)
        StellarNetSpectrum_700_800nm = hdf.create_dataset('StellarNetSpectrum_700_800nm', data=data_stellar5)
        Ocilloscope_data = hdf.create_dataset('Ocilloscope_data', data=data_oci)

        abs_pos = [self.x_xps.getStagePosition(self.x_axis), self.y_xps.getStagePosition(self.y_axis)]
        hdf.attrs['LaserEnergy'] = self.Laser_Energy
        hdf.attrs['LaserWavelength'] = self.Laser_Wavelength
        hdf.attrs['LaserPulseDuration'] = self.Laser_PulseDuration
        hdf.attrs['SampleType'] = self.Sample_Type
        hdf.attrs['FocalLength'] = self.Focal_Length
        hdf.attrs['IntegrationTime'] = self.Integration_Time
        hdf.attrs['FiberAngle'] = self.Fiber_Angle
        hdf.attrs['BackgroundSpectrum'] = self.Background_Spectrum
        hdf.attrs['AbsoluteStageLocation'] = abs_pos
        hdf.attrs['OtherNotes'] = self.Other_Notes
        hdf.close()
            
        self.file_num += 1
        
# STAGE CONTROL ----------------------------------------------------------------------
        if self.same_loc_shot == self.num_shots_same_loc:
            if self.step_count == self.num_shots:
                self.end_timer()
                self.same_loc_shot =1
                return
            
            if self.step_count%self.max_cols!=0 and self.rows%2==0:
                self.x_xps.moveRelative(self.x_axis, self.step_length)
            if self.step_count%self.max_cols!=0 and self.rows%2!=0:
                self.x_xps.moveRelative(self.x_axis, 0-self.step_length)
            elif self.step_count%self.max_cols == 0:
                self.y_xps.moveRelative(self.y_axis, self.step_length)
                self.rows += 1
            self.step_count += 1
           
            self.same_loc_shot =1
            
            self.print_location()
            msg = 'number of steps taken: ' + str(self.step_count)
            self.messages.setText(msg)
            
        else:
            self.same_loc_shot +=1
#---------------------------------------------------------------------------------------
    def reset(self, spectrometer):
        spectrometer['device'].__del__()
    
    def DisconnectAll(self):
        ins.sendcmd('IFRS 0') #close dg 645
        # spec.close() # close thorlabs
        self.reset(spectrometer0) # close stellarNet
        self.reset(spectrometer1)
        self.reset(spectrometer2)
        self.reset(spectrometer3) 
        self.reset(spectrometer4)
        self.reset(spectrometer5)
        sn.uninstallDeviceDriver()

# STAGE CONTROL ---------------------------------------------------------------------

        
    def print_location(self):
        '''
        Prints the absolute and relative location of the 2 actuators. Also checks actuator 
        status and enables/disables accordingly.
        '''
        abs = [self.x_xps.getStagePosition(self.x_axis), self.y_xps.getStagePosition(self.y_axis)]
        self.abs_lbl.setText(str(abs[0])+", "+str(abs[1]))
        self.rel_lbl.setText(str(abs[0]-self.ref[0])+", "+str(abs[1]-self.ref[1]))
        
        self.update_status(self.x_xps.getStageStatus(self.x_axis))
        
    def set_minmax(self, axis, setting, val):
        '''
        Sets the minimum and maximum points of travel.
        
        Parameters
        ----------
        axis (string) : The axis of travel that the actuator will be moving along. Either "x" for 
                        x-axis or "y" for y-axis
        setting (string) : Setting of whether to set a minimum or maximum. "min" for minimum, 
                           "max" for maximum.
        val (string) : The value to set the minimum or maximum point as. Defaults to 0 for minumum 
                       and 50 for maximum if nothing is inputted.
        '''
        inst = self.x_xps if axis=="x" else self.y_xps
        group = self.x_axis if axis=="x" else self.y_axis
        
        if setting == "min":
            val = 0 if val=="" else float(val)
            inst.setminLimit(group, val)
        elif setting == "max":
            val = 50 if val=="" else float(val)
            inst.setmaxLimit(group, val)

    def update_group(self, axis):
        '''
        Sets and gets the status of a new actuator group after changing actuators.
        
        Parameters
        ----------
        axis (string) : The axis of travel that the actuator will be moving along. Either "X" for 
                        x-axis or "Y" for y-axis
        '''
        self.xps_groups = self.x_xps.getXPSStatus()
        if axis == "X": 
            self.x_axis = str(self.x_group_combo.currentText())
            self.x_xps.setGroup(self.x_axis)
            self.update_status(self.x_xps.getStageStatus(self.x_axis))
            
        elif axis == "Y":
            self.y_axis = str(self.y_group_combo.currentText())
            self.y_xps.setGroup(self.y_axis)
            self.update_status(self.y_xps.getStageStatus(self.y_axis))
   
    def update_status(self, stage_status):
        '''
        Enables and disables buttons according to the status of the two actuators.
        
        Parameters
        ----------
        stage_status (string) : status of the XPS actuator.
        '''
        if stage_status == "Not initialized state" \
            or stage_status == "Not initialized state due to a GroupKill or KillAll command" \
            or stage_status == "Not referenced state":
                
            for widget in self.translationStage.children():
                if not isinstance(widget, (QtCore.QTimer, QtGui.QDoubleValidator, QtGui.QIntValidator)):
                    widget.setEnabled(False)
            self.initialize_btn.setEnabled(True)
            self.messages.setText("Not Initialized")

        elif stage_status == "Disabled state":
            for widget in self.translationStage.children():
                if not isinstance(widget, (QtCore.QTimer, QtGui.QDoubleValidator, QtGui.QIntValidator)):
                    widget.setEnabled(False)
            self.enable_btn.setEnabled(True)
            self.enable_btn.setText("Enable")

        # Initialized and enabled
        elif stage_status[:11].upper() == "Ready state".upper():
            for widget in self.translationStage.children():
                if not isinstance(widget, (QtCore.QTimer, QtGui.QDoubleValidator, QtGui.QIntValidator)):
                    if widget != self.num_shots_line and widget != self.raster_btn:
                        widget.setEnabled(True)
            self.enable_btn.setText("Disable")

    def initialize(self):
        '''
        Initializes and homes both selected actuators.
        '''
        self.x_xps.initializeStage(self.x_axis)
        self.x_xps.homeStage(self.x_axis)
        self.y_xps.initializeStage(self.y_axis)
        self.y_xps.homeStage(self.y_axis)
        
        self.update_status(self.x_xps.getStageStatus(self.x_axis))
        self.update_status(self.y_xps.getStageStatus(self.y_axis))
        
    def kill(self):
        '''
        Kills both selected actuators.
        '''
        self.x_xps.killAll(self.x_axis)
        self.y_xps.killAll(self.y_axis)
        
        self.update_status(self.x_xps.getStageStatus(self.x_axis))
        self.update_status(self.y_xps.getStageStatus(self.y_axis))

    def enable_disable(self):
        '''
        Enables or disables both selected actuators depending on its status.
        '''
        if self.x_xps.getStageStatus(self.x_axis).upper() == "Disabled state".upper() \
            or self.y_xps.getStageStatus(self.y_axis).upper() == "Disabled state".upper():
            self.x_xps.enableGroup(self.x_axis)
            self.y_xps.enableGroup(self.y_axis)
        elif self.x_xps.getStageStatus(self.x_axis)[:11].upper() == "Ready state".upper() \
            or self.y_xps.getStageStatus(self.y_axis)[:11].upper() == "Ready state".upper():
            self.x_xps.disableGroup(self.x_axis)
            self.y_xps.disableGroup(self.y_axis)
            
        self.update_status(self.x_xps.getStageStatus(self.x_axis))
        self.update_status(self.y_xps.getStageStatus(self.y_axis))

    def relative(self, btn):
        '''
        Controls relative movements of the stage (relative stepping left, right, up, down).
        
        Parameters
        ----------
        btn (string) : Button pressed that determines the direction of step.
        '''
        if self.rel_line.text():
            # Gets the step length to step relatively by
            dist = float(self.rel_line.text())
            
            if btn == 'left':
                self.x_xps.moveRelative(self.x_axis, 0-dist)
            elif btn == 'right':
                self.x_xps.moveRelative(self.x_axis, dist)
            if btn == 'up':
                self.y_xps.moveRelative(self.y_axis, dist)
            if btn == 'down':
                self.y_xps.moveRelative(self.y_axis, 0-dist)
            
    def ref_commands(self, cmd):
        '''
        Controls commands relating to the reference point of the stage.
        
        Parameters
        ----------
        cmd (string) : Button pressed that determines what command to trigger ("set" or "return").
        '''
        if cmd == 'set':
            self.ref = [self.x_xps.getStagePosition(self.x_axis), self.y_xps.getStagePosition(self.y_axis)]
        elif cmd == 'return':
            self.x_xps.moveAbsolute(self.x_axis, self.ref[0])
            self.y_xps.moveAbsolute(self.y_axis, self.ref[1])
    
    def absolute(self):
        '''
        Controls absolute movements of the stage. X and y-axes can move absolutely 
        independantly of eachother.
        '''
        if self.abs_x_line.text():
            pos = float(self.abs_x_line.text())
            self.x_xps.moveAbsolute(self.x_axis, pos)
        if self.abs_y_line.text():
            pos = float(self.abs_y_line.text())
            self.y_xps.moveAbsolute(self.y_axis, pos)

    def raster_inp(self, inp):
        '''
        Checks and validates the inputs given to raster. Also clears the number of shots line
        after editing other inputs and enables/disables the raster button depending on whether
        all inputs have been entered.
        
        Parameters
        ----------
        inp (string) : LineEdit box that was edited.
        '''
        self.messages.clear()
        
        if inp == 'step_length':
            if self.step_length_line.text():
                self.step_length = float(self.step_length_line.text())
        elif inp == 'sample_length':
            max_length = self.abs_max[0] - self.ref[0]
            if self.sample_length_line.text():
                if float(self.sample_length_line.text()) > max_length:
                    self.sample_length_line.setText(str(max_length))
                self.sample_length = float(self.sample_length_line.text())
        elif inp == 'sample_width':
            max_width = self.abs_max[1] - self.ref[1]
            if self.sample_width_line.text():
                if float(self.sample_width_line.text()) > max_width:
                    self.sample_width_line.setText(str(max_width))
                self.sample_width = float(self.sample_width_line.text())
        elif inp == 'set_bound_x':
            self.sample_length = np.abs(self.x_xps.getStagePosition(self.x_axis) - self.ref[0])
            self.sample_length_line.setText(str(self.sample_length))
        elif inp == 'set_bound_y':
            self.sample_width = np.abs(self.y_xps.getStagePosition(self.y_axis) - self.ref[1])
            self.sample_width_line.setText(str(self.sample_width))
        elif inp == "shots_same_loc":
            try:
                self.num_shots_same_loc = int(self.num_shots_same_loc_txt.text())
            except:
                self.num_shots_same_loc = 1
                return
            # self.total_shots_2.setText(str(self.num_shots_same_loc*self.num_shots))
        elif inp == 'num_shots':
            if self.num_shots_line.text():
                self.num_shots = int(self.num_shots_line.text())
            if self.step_length_line.text() and self.sample_length_line.text() \
                and self.sample_width_line.text() and not self.messages.text():
                self.raster_btn.setEnabled(True)
            # self.total_shots_2.setText(str(self.num_shots_same_loc*self.num_shots))
            return

        
        # Clears num shots line if other inputs have been changed.
        self.num_shots_line.clear()
        self.raster_btn.setEnabled(False)
        self.num_shots_line.setEnabled(False)
        
        # Calculates the maximum number of shots if all inputs have been filled.
        if self.step_length_line.text() and self.sample_length_line.text() and self.sample_width_line.text():
            if self.step_length == 0:
                self.messages.setText('ERROR: step length cannot be 0')
                return
            if self.step_length > self.sample_length:
                self.messages.setText('ERROR: step cannot be greater than sample length')
                return
            if self.step_length > self.sample_width:
                self.messages.setText('ERROR: step cannot be greater than sample width')
                return
            self.max_cols = floor(Fraction(self.sample_length)/Fraction(self.step_length))
            self.max_rows = floor(Fraction(self.sample_width)/Fraction(self.step_length))
            self.max_shots = self.max_rows * self.max_cols
            self.max_shots_lbl.setText(str(self.max_shots))
            self.num_shots_line.setValidator(QtGui.QIntValidator(1, self.max_shots, self))
            
            self.num_shots_line.setEnabled(True)

            
    def start_timer(self):
        '''
        Moves stage to initial position (half a step away from home) and starts timer for raster.
        If no rep rate was given, will assume 0 s.
        '''
        if self.half_step.isChecked():
            self.x_xps.moveAbsolute(self.x_axis, self.ref[0] + self.step_length/2)
            self.y_xps.moveAbsolute(self.y_axis, self.ref[1] + self.step_length/2)
        
        self.step_count = 1
        self.rows = 0
        
        self.intigration_time_thor = int(self.thorlabs_inti_time.toPlainText())
        self.inttime = int(self.stellarNet_inti_time.toPlainText())
        
        self.print_location()
        msg = 'number of steps taken: ' + str(self.step_count)
        self.messages.setText(msg)
        
        if self.rep_rate_line.text():
            rep_rate = int(float(self.rep_rate_line.text()) * 1000)
        else: 
            rep_rate = 0
        
        # self.rast_timer = QtCore.QTimer(self, interval = rep_rate, timeout = self.raster)
        self.rast_timer = QtCore.QTimer(self, interval = rep_rate, timeout = self.MySpectrometers)
        self.rast_timer.start()
            
    def raster(self):
        '''
        Takes a step and prints location and number of steps taken.
        '''
        if self.step_count%self.max_cols!=0 and self.rows%2==0:
            self.x_xps.moveRelative(self.x_axis, self.step_length)
        if self.step_count%self.max_cols!=0 and self.rows%2!=0:
            self.x_xps.moveRelative(self.x_axis, 0-self.step_length)
        elif self.step_count%self.max_cols == 0:
            self.y_xps.moveRelative(self.y_axis, self.step_length)
            self.rows += 1
        self.step_count += 1
        
        self.print_location()
        msg = 'number of steps taken: ' + str(self.step_count)
        self.messages.setText(msg)
        
        if self.step_count == self.num_shots:
            self.end_timer()
            
    def end_timer(self):
        '''
        Kills raster timer and resets values.
        '''
        self.rast_timer.stop()
        del self.rast_timer
        
        self.rows = 0
        self.step_count = 1
# -------------------------------------------------------------------------------------  

#Ocilloscope -------------------------------------------------------------------------------------     
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
        elif inp == 'trig_source':
            if self.trig_source_line.text():
                self.trig_source = (self.trig_source_line.text())
        elif inp == 'rec_length':
            if self.rec_length_line.text():
                self.rec_length = (self.rec_length_line.text())
        elif inp == 'v_div':
            if self.v_div_line.text():
                self.v_div = (self.v_div_line.text())
        elif inp == 't_div':
            if self.t_div_line.text():
                self.t_div = (self.t_div_line.text())




        
# -------------------------------------------------------------------------------------  
        
    def closeEvent(self, event):
        '''
        Kills timers and saves gui inputs to .json file before killing application.
        '''
        self.print_timer.stop()
        del self.print_timer
        
        try:
            self.rast_timer.stop()
            del self.rast_timer
        except:
            pass
        
        self.write_json()
        event.accept()


        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.exec_()
    # sys.exit(app.exec_())