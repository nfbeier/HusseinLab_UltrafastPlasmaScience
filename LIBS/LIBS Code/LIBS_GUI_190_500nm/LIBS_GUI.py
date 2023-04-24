# LIBS GUI v5, 2022-06-03
# Shubho Mohajan, Ying Wan, Dr. Nicholas Beier, Dr. Amina Hussein
# University of Alberta, ECE Department

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys, threading, h5py
from fractions import Fraction

from pyqtgraph import PlotWidget
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k') 

from stage_control import Motor, Control
from math import floor
import manipulate_json

#importing resources for DG645
import instruments as ik
import quantities as pq
      
#importing resources for thorlabs
import pyvisa
from instrumental import instrument, list_instruments
from instrumental.drivers.spectrometers import thorlabs_ccs
import matplotlib.pyplot as plt
rm = pyvisa.ResourceManager()
res = rm.list_resources('?*::?*')

#importing resources for stellerNet
import time, logging
import numpy as np
# import the usb driver
import stellarnet_driver3 as sn
import matplotlib.pyplot as plt
logging.basicConfig(format='%(asctime)s %(message)s')

#GUI Design file importing here (qt design file)
qtcreator_file  = "LIBS_GUI.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

#Connecting all hardwares
ins = ik.srs.SRSDG645.open_serial('COM12', 9600) # dg645
paramsets = list_instruments()
spec = instrument(paramsets[0],reopen_policy = "new")# thorlabs ccs200
spectrometer, wav = sn.array_get_spec(0) # stellerNet
scansavg = 1
smooth = 1

#Global variables for data saving and plotting
wave = None # wavelength for thorlab
data_thor = None # intensity for thorlab
data_stellar = None # wavelength and intensity for stellerNet
wave_thor_all = np.zeros((3648, 2)) # for storing previous shot thorlab wavelength 
intensity_thor_all = np.zeros((3648, 2))  # for storing previous shot thorlab intensity
# wave_steller_all = np.zeros((2048, 2))
intensity_steller_all = np.zeros((2048, 2)) # for storing previous shot stellernet intenssity

# Thread class for each hardware 
class ThorlabsTriggerThread(threading.Thread):
    def __init__(self, intigration_time_thor):
        super(ThorlabsTriggerThread,self).__init__()
        self.intigration_time_thor  = intigration_time_thor
        global wave, data_thor
        spec.set_integration_time(str(intigration_time_thor)+' ms')
        spec.start_scan_trg()
        wave = spec._wavelength_array
        data_thor = spec.get_scan_data()


class StellerNetTriggerThread(threading.Thread):
    def __init__(self, inttime):
        super(StellerNetTriggerThread,self).__init__()
        self.inttime = inttime
        global data_stellar
        logging.warning('displaying spectrum')
        self.external_trigger(spectrometer,True)
        data_stellar = self.getSpectrum(spectrometer, wav, inttime, scansavg, smooth)

    #function for getting spectrum from stellArNet
    def getSpectrum(self, spectrometer, wav, inttime, scansavg, smooth):
        logging.warning('requesting spectrum')
        spectrometer['device'].set_config(int_time=inttime, scans_to_avg=scansavg, x_smooth=smooth)
        spectrum = sn.array_spectrum(spectrometer, wav)
        logging.warning('recieved spectrum')
        return spectrum 

    # function external triger of stellarNet    
    def external_trigger(self,spectrometer,trigger):
        sn.ext_trig(spectrometer,trigger)


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
        manipulate_json.read_json(self)
        self.MetaData()

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
        self.Start.clicked.connect(self.start_raster)
        self.disconnect_all.clicked.connect(self.DisconnectAll)

        self.plot_graph.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph.showAxis('right')
        self.plot_graph.showAxis('top')
        self.plot_graph.getAxis('top').setStyle(showValues=False)
        self.plot_graph.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_2.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_2.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_2.showAxis('right')
        self.plot_graph_2.showAxis('top')
        self.plot_graph_2.getAxis('top').setStyle(showValues=False)
        self.plot_graph_2.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_3.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_3.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_3.showAxis('right')
        self.plot_graph_3.showAxis('top')
        self.plot_graph_3.getAxis('top').setStyle(showValues=False)
        self.plot_graph_3.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_4.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_4.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_4.showAxis('right')
        self.plot_graph_4.showAxis('top')
        self.plot_graph_4.getAxis('top').setStyle(showValues=False)
        self.plot_graph_4.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_5.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_5.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_5.showAxis('right')
        self.plot_graph_5.showAxis('top')
        self.plot_graph_5.getAxis('top').setStyle(showValues=False)
        self.plot_graph_5.getAxis('right').setStyle(showValues=False)
        
        self.plot_graph_6.setLabel(axis='left', text='Intensity (a.u)')
        self.plot_graph_6.setLabel(axis='bottom', text='Wavelength (nm)')
        self.plot_graph_6.showAxis('right')
        self.plot_graph_6.showAxis('top')
        self.plot_graph_6.getAxis('top').setStyle(showValues=False)
        self.plot_graph_6.getAxis('right').setStyle(showValues=False)

        # STAGE CONTROL ----------------------------------------------------------------------

        coord, home = self.init_stage_vals()
        self.motor = Motor(coord, home)
        self.control = Control()
        # Show coordinate of stage on startup
        self.print_location()

        # manual
        manual_step_length = float(self.manual_step_length_txt.text())
        self.left_btn.clicked.connect(lambda: self.manual("left", float(self.manual_step_length_txt.text())))
        self.right_btn.clicked.connect(lambda: self.manual("right", float(self.manual_step_length_txt.text())))
        self.up_btn.clicked.connect(lambda: self.manual("up", float(self.manual_step_length_txt.text())))
        self.down_btn.clicked.connect(lambda: self.manual("down", float(self.manual_step_length_txt.text())))
        self.set_home_btn.clicked.connect(lambda: self.manual("set", 0))
        self.return_home_btn.clicked.connect(lambda: self.manual("return", 0))

        # raster inputs
        self.sample_width = float(self.sample_width_txt.text())
        self.sample_width_txt.textEdited.connect(lambda: self.raster_inp("sample width"))
        self.sample_height = float(self.sample_height_txt.text())
        self.sample_height_txt.textEdited.connect(lambda: self.raster_inp("sample height"))
        self.step_length = float(self.step_length_txt.text())
        self.step_length_txt.textEdited.connect(lambda: self.raster_inp("step length"))
        self.num_shots = float(self.num_shots_txt.text())
        self.num_shots_txt.textEdited.connect(lambda: self.raster_inp("shots"))
        
        # manually set bounds for raster
        self.set_xbound_btn.clicked.connect(lambda: self.set_limits("x"))
        self.set_ybound_btn.clicked.connect(lambda: self.set_limits("y"))
        
        try:
            self.max_cols = floor(Fraction(str(self.sample_width))/Fraction(str(self.step_length)))
        except:
            self.message.setText("error in inputs")
        try:
            self.max_rows = floor(Fraction(str(self.sample_height))/Fraction(str(self.step_length)))
        except:
            pass

        try:
            self.max_shots = self.max_cols * self.max_rows
        except:
            pass
        
        self.file_num = 1
        # -------------------------------------------------------------------------------------
    
    def MetaData(self):
        #self.Laser_Energy =0 
        self.Laser_Energy =float(self.LaserEnergy.toPlainText())
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
         ins.channel["H"].delay = (ins.channel[self.H_ch.toPlainText()], pq.Quantity(float(self.G_delay.toPlainText()), self.H_delay_unit.toPlainText()))
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
        
    def start_raster(self):
        '''
        Initializes stage location and spectrometer values. Starts the timer for rastering/"single shot". 
        '''
        self.manual("up", self.step_length/2)
        self.manual("left", self.step_length/2)
        
        self.intigration_time_thor = int(self.thorlabs_inti_time.toPlainText())
        self.inttime = int(self.stellarNet_inti_time.toPlainText())
        
        self.rows = 0
        self.step_count = 1
        self.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)
        
        self.timer = QtCore.QTimer(self, interval = self.step_length/10, timeout = self.MySpectrometers)
        self.timer.start()
        
    def MySpectrometers(self):
        # Calling hardware threads   
        ThorlabsTrigThread = threading.Thread(target=ThorlabsTriggerThread, args=(self.intigration_time_thor, ))
        StellerNetTrigThread = threading.Thread(target=StellerNetTriggerThread, args=(self.inttime, ))
        Fire = threading.Thread(target=FireThread, args=(10, ))

        # Start Parallel Operation of hardwares
        ThorlabsTrigThread.start()
        StellerNetTrigThread.start()
        time.sleep(1)
        Fire.start()
        
        ThorlabsTrigThread.join()
        StellerNetTrigThread.join()
        Fire.join()        
        
        # calling variables for sending data from thread
        global wave
        global data_thor
        global data_stellar
        global wave_thor_all
        global intensity_thor_all
        global intensity_steller_all
        
        wave = np.array([wave])
        data_thor = np.array([data_thor])
        
        # Cascading data for previous shots
        wave_thor_all = np.hstack([wave_thor_all, wave.T])
        intensity_thor_all = np.hstack([intensity_thor_all, data_thor.T])
        temp_steller = data_stellar[:,1].reshape(2048,1)
        intensity_steller_all = np.hstack([intensity_steller_all, temp_steller])
        
        #plotting
        self.plot_graph.clear()
        self.plot_graph.plot(wave_thor_all[:,-1], intensity_thor_all[:, -1], pen='b')

        self.plot_graph_2.clear()
        self.plot_graph_2.plot(wave_thor_all[:,-2], intensity_thor_all[:, -2], pen='b')

        self.plot_graph_3.clear()
        self.plot_graph_3.plot(wave_thor_all[:,-3], intensity_thor_all[:, -3], pen='b')

        self.plot_graph_4.clear()
        self.plot_graph_4.plot(data_stellar[:,0],intensity_steller_all[:,-1], pen='b')

        self.plot_graph_5.clear()
        self.plot_graph_5.plot(data_stellar[:,0],intensity_steller_all[:,-2], pen='b')

        self.plot_graph_6.clear()
        self.plot_graph_6.plot(data_stellar[:,0],intensity_steller_all[:,-3], pen='b')
        
        # Deleting 4th shot data for memory efficiencyy 
        wave_thor_all = np.delete(wave_thor_all, 0, 1)
        intensity_thor_all = np.delete(intensity_thor_all, 0, 1)
        intensity_steller_all = np.delete(intensity_steller_all, 0, 1)
        
        #Save Data in 
        data_thor_zip = np.hstack([wave.T, data_thor.T])
        # txtnum = self._submit_counter
        txtnum = self.file_num
        # print(txtnum)
        path_SaveData = self.SaveData_dir.toPlainText()
        hdf = h5py.File (path_SaveData + '/'  + time.strftime("%Y%m%d")+'_LIBS_Spectrum_{}.h5'.format(txtnum), 'w')
        ThorlabsSpectrum = hdf.create_dataset('ThorlabsSpectrum', data=data_thor_zip)
        StellarNetSpectrum = hdf.create_dataset('StellarNetSpectrum', data=data_stellar)

        hdf.attrs['LaserEnergy'] = self.Laser_Energy
        hdf.attrs['LaserWavelength'] = self.Laser_Wavelength
        hdf.attrs['LaserPulseDuration'] = self.Laser_PulseDuration
        hdf.attrs['SampleType'] = self.Sample_Type
        hdf.attrs['FocalLength'] = self.Focal_Length
        hdf.attrs['IntegrationTime'] = self.Integration_Time
        hdf.attrs['FiberAngle'] = self.Fiber_Angle
        hdf.attrs['BackgroundSpectrum'] = self.Background_Spectrum
        hdf.attrs['AbsoluteStageLocation'] = self.motor.get_coord()
        hdf.attrs['OtherNotes'] = self.Other_Notes
        hdf.close()
            
        self.file_num += 1
        
        if self.step_count == self.num_shots:
            self.end_raster()
            return
            
        if self.step_count % self.max_cols == 0:
            self.manual("up", self.step_length)
            self.rows += 1
        elif self.rows % 2 == 0:
            self.manual("left", self.step_length)
        elif self.rows % 2 != 0:
            self.manual("right", self.step_length)
     
        self.step_count += 1
        self.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)

    def end_raster(self):
        '''
        Stops and deletes timer.

        '''
        self.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)
        
        self.timer.stop()
        self.step_count = 1
        del self.timer
 
    def reset(self, spectrometer):
        spectrometer['device'].__del__()
    
    def DisconnectAll(self):
        ins.sendcmd('IFRS 0') #close dg 645
        spec.close() # close thorlabs
        self.reset(spectrometer) # close stellarNet

    # STAGE CONTROL ---------------------------------------------------------------------

    def init_stage_vals(self):
        '''
        Reads in coordinate and home coordinate of the stage's last usage. Read in from
        stage_location.txt. 
        WARNING: the file location is absolute. Do not move folder.
        Returns
        -------
        coord (float): Absolute coordinate of stage location.
        home (float): Absolute coordinate of home location.
        '''
        abs_x, abs_y = self.abs_location_lbl.text().split(", ")
        rel_x, rel_y = self.rel_location_lbl.text().split(", ")
        
        coord = [float(abs_x), float(abs_y)]
        home = [float(abs_x) - float(rel_x), float(abs_y) - float(rel_y)]
        return coord, home 
        
    def print_location(self):
        '''
        Prints relative and absolute stage position onto gui.
        '''
        coord = self.motor.get_coord()
        home = self.motor.get_home()
        rel = str(coord[0] - home[0]) + ", " + str(coord[1] - home[1])
        self.rel_location_lbl.setText(rel)
        self.abs_location_lbl.setText(str(coord[0]) + ", " + str(coord[1]))
        
        if self.rel_location_lbl.text() != "0.0, 0.0":
            self.Start.setEnabled(False)
            self.raster_btn.setEnabled(False)
        else:
            self.Start.setEnabled(True)
            self.raster_btn.setEnabled(True)

    def manual(self, btn, dist):
        '''
        Executes manual controls: moves left and right, sets home, returns home.
        Also prints errors and absolute and relative locations.
        Parameters
        ----------
        btn (string): Button pressed in gui.
        '''
        self.messages_lbl.setText("")
        coord = self.motor.get_coord()

        if btn == "left":
            if (coord[0] - dist) >= self.motor.get_min()[0]:
                self.control.right(self.motor, dist)
            else:
                self.messages_lbl.setText("ERROR: reached end stop limit")
        elif btn == "right":
            if (coord[0] + dist) <= self.motor.get_max()[0]:
                self.control.left(self.motor, dist)
            else:
                self.messages_lbl.setText("ERROR: reached end stop limit")
        elif btn == "up":
            if (coord[1] - dist) >= self.motor.get_min()[1]:
                self.control.up(self.motor, dist)
            else:
                self.messages_lbl.setText("ERROR: reached end stop limit")
        elif btn == "down":
            if (coord[1] + dist) <= self.motor.get_max()[1]:
                self.control.down(self.motor, dist)
            else:
                self.messages_lbl.setText("ERROR: reached end stop limit")
        elif btn == "set":
            self.motor.set_home(self.motor.get_coord()[0], self.motor.get_coord()[1])
        elif btn == "return":
            self.control.return_home(self.motor)

        self.print_location()

    def set_limits(self, btn):
        '''
        Calibrates sample size based on the distance between home and current stage location.

        Parameters:
        -----------
        btn (string): Indicates which button was hit and whether to calibrate the x or y axis
        '''
        if btn == "x":
            self.sample_width = abs(self.motor.get_coord()[0] - self.motor.get_home()[0])
            self.sample_width_txt.setText(str(self.sample_width))
        elif btn == "y":
            self.sample_height = abs(self.motor.get_coord()[1] - self.motor.get_home()[1])
            self.sample_height_txt.setText(str(self.sample_height))

    def check_inp(self, inp, max_val):
        # Checks if input is an integer, gui will crash otherwise
        try:
            self.messages_lbl.setText("")
            val = float(inp)
            if val > max_val:
                self.messages_lbl.setText("ERROR: input exceeds maximum")
                val = max_val  # Assume sample length is distance from home to end stops
            return val
        except:
            self.messages_lbl.setText("ERROR: invalid input")
            self.enable("raster btn", False)
            return 0

    def raster_inp(self, inp):
        '''
        Takes input for raster controls: takes input for step length and sample length, calculates 
        number of max shots, takes input for number of shots.
        
        Parameters
        ----------
        inp (string): Textbox edited in gui.
        '''
        max_width = self.motor.get_max()[0] - abs(self.motor.get_home()[0])
        max_height = self.motor.get_max()[1] - self.motor.get_home()[1]
        
        if inp == "sample width":
            # Checks if input is an integer, gui will crash without the try and except
            # sample_width = float(self.sample_width_txt.text())
            try:
                sample_width = float(self.sample_width_txt.text())
            except:
                self.messages_lbl.setText("ERROR: invalid input")
                self.sample_width = 0
                return
            if sample_width > max_width:
                self.messages_lbl.setText("ERROR: sample length exceeds end stops")
                # Assume sample length is distance from home to end stops
                self.sample_width = max_width
                self.sample_width_txt.setText(str(self.sample_width))
            else:
                self.sample_width = sample_width
                
        if inp == "sample height":
            # Checks if input is an integer, gui will crash without the try and except
            try:
                sample_height = float(self.sample_height_txt.text())
            except:
                self.messages_lbl.setText("ERROR: invalid input")
                self.sample_height = 0
                return
            if sample_height > max_height:
                self.messages_lbl.setText("ERROR: sample length exceeds end stops")
                # Assume sample length is distance from home to end stops
                self.sample_height = max_height
                self.sample_height_txt.setText(str(self.sample_height))
            else:
                self.sample_height = sample_height
                
        elif inp == "step length":
            try:
                step_length = float(self.step_length_txt.text())
            except:
                self.messages_lbl.setText("ERROR: invalid input")
                self.step_length = 0
                return
            if step_length > max_width:
                self.messages_lbl.setText("ERROR: step length exceeds end stops")
                # Assume step length is distance from home to end stops
                self.step_length = max_width
                self.step_length_txt.setText(str(self.step_length))
            elif step_length > max_height:
                self.messages_lbl.setText("ERROR: step length exceeds end stops")
                # Assume step length is distance from home to end stops
                self.step_length = max_height
                self.step_length_txt.setText(str(self.step_length))
            # Will throw an error later since division by 0 is not allowed 
            elif step_length != 0:
                self.step_length = step_length

        elif inp == "shots":
            try:
                num_shots = float(self.num_shots_txt.text())
            except:
                self.messages_lbl.setText("ERROR: invalid input")
                self.num_shots = 0
                return

            if num_shots > self.max_shots:
                self.messages_lbl.setText("ERROR: input cannot be greater than maximum.")
                # Assume number of shots is the max.
                self.num_shots = self.max_shots
                self.num_shots_txt.setText(str(self.num_shots))
            else:
                self.num_shots = num_shots

        # Can only run once both lengths have been inputted, or else gui will crash.
        if self.sample_width_txt.text() != "" and self.step_length_txt.text() != "":
            if self.step_length > self.sample_width:
                self.messages_lbl.setText("ERROR: step length is larger than sample length")
                # Assume step length is equal to sample length.
                self.step_length = self.sample_width
                self.step_length_txt.setText(str(self.step_length))
            # Float division will sometimes floor/round incorrectly without using Fraction.
            self.max_cols = floor(Fraction(str(self.sample_width))/Fraction(str(self.step_length)))
            
        if self.sample_height_txt.text() != "" and self.step_length_txt.text() != "":
            if self.step_length > self.sample_height:
                self.messages_lbl.setText("ERROR: step length is larger than sample length")
                # Assume step length is equal to sample length.
                self.step_length = self.sample_height
                self.step_length_txt.setText(str(self.step_length))
            self.max_rows = floor(Fraction(str(self.sample_height))/Fraction(str(self.step_length)))

        try:
            self.max_shots = self.max_cols * self.max_rows
        except:
            self.max_shots = 0

        self.max_lbl.setText(str(self.max_shots))
        
    def start_test_raster(self):
        '''
        Initializes stage location and spectrometer values. Starts the timer for rastering/"single shot". 
        '''
        self.manual("up", self.step_length/2)
        self.manual("left", self.step_length/2)
        self.rows = 0
        self.step_count = 1
        self.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)
        
        self.timer = QtCore.QTimer(self, interval = self.step_length/10, timeout = self.test_raster)
        self.timer.start()

    def test_raster(self):
        if self.step_count == self.num_shots:
            self.end_raster()
            return
        
        if self.step_count !=0 and self.step_count % self.max_cols == 0:
            self.manual("up", self.step_length)
            self.rows += 1
        elif self.rows % 2 == 0:
            self.manual("left", self.step_length)
        elif self.rows % 2 != 0:
            self.manual("right", self.step_length)
            
        self.step_count += 1
        self.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)
        
        time.sleep(1)
            
    def closeEvent(self, event):
        try:
            self.end_raster()
        except:
            pass
        
        manipulate_json.write_json(self)
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.exec_()