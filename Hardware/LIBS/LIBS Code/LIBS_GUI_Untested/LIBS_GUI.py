# LIBS GUI v5, 2022-06-03
# Shubho Mohajan, Ying Wan, Dr. Nicholas Beier, Dr. Amina Hussein
# University of Alberta, ECE Department

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys, threading, h5py

from NEMA_GUI import NEMA
from DG645_GUI import DelayGenerator 
from SPEC_GUI import Spectrometers

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
    def __init__(self, clicked, dg):
        super(FireThread, self).__init__()
        self.clicked = clicked
        dg.send_command('TSRC 5') 
        dg.send_command('*TRG')


# Main class for GUI
class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Delay Generator
        self.dg = DelayGenerator(self)
        self.delay_combo.currentTextChanged.connect(lambda: self.dg.edit_ch("delay"))
        self.voltage_combo.currentTextChanged.connect(lambda: self.dg.edit_ch("voltage"))
        self.channel_line.textEdited.connect(lambda: self.dg.edit_val("channel"))
        self.delay_line.textEdited.connect(lambda: self.dg.edit_val("delay"))
        self.unit_line.textEdited.connect(lambda: self.dg.edit_val("unit"))
        self.offset_line.textEdited.connect(lambda: self.dg.edit_val("offset"))
        self.amplitude_line.textEdited.connect(lambda: self.dg.edit_val("amplitude"))
        self.T0_disp.clicked.connect(lambda: self.dg.change_display("T0"))
        self.T1_disp.clicked.connect(lambda: self.dg.change_display("T1"))
        self.A_disp.clicked.connect(lambda: self.dg.change_display("A"))
        self.B_disp.clicked.connect(lambda: self.dg.change_display("B"))
        self.C_disp.clicked.connect(lambda: self.dg.change_display("C"))
        self.D_disp.clicked.connect(lambda: self.dg.change_display("D"))
        self.E_disp.clicked.connect(lambda: self.dg.change_display("E"))
        self.F_disp.clicked.connect(lambda: self.dg.change_display("F"))
        self.G_disp.clicked.connect(lambda: self.dg.change_display("G"))
        self.H_disp.clicked.connect(lambda: self.dg.change_display("H"))
        
        self.spec = Spectrometers(self)

        # Stage
        self.NEMA = NEMA(self)
        self.left_btn.clicked.connect(lambda: self.NEMA.manual("left", float(self.manual_step_length_txt.text())))
        self.right_btn.clicked.connect(lambda: self.NEMA.manual("right", float(self.manual_step_length_txt.text())))
        self.up_btn.clicked.connect(lambda: self.NEMA.manual("up", float(self.manual_step_length_txt.text())))
        self.down_btn.clicked.connect(lambda: self.NEMA.manual("down", float(self.manual_step_length_txt.text())))
        self.set_home_btn.clicked.connect(lambda: self.NEMA.manual("set", 0))
        self.return_home_btn.clicked.connect(lambda: self.NEMA.manual("return", 0))
        self.sample_width_txt.textEdited.connect(lambda: self.NEMA.raster_inp("sample width"))
        self.sample_height_txt.textEdited.connect(lambda: self.NEMA.raster_inp("sample height"))
        self.step_length_txt.textEdited.connect(lambda: self.NEMA.raster_inp("step length"))
        self.num_shots_txt.textEdited.connect(lambda: self.NEMA.raster_inp("shots"))
        self.set_xbound_btn.clicked.connect(lambda: self.NEMA.set_limits("x"))
        self.set_ybound_btn.clicked.connect(lambda: self.NEMA.set_limits("y"))
        # self.raster_btn.clicked.connect(self.NEMA.start_test_raster)
        
        self.file_num = 1  # Counter to label hdf5 files

        self.Start.clicked.connect(self.start_raster)
        self.stop_btn.clicked.connect(self.end_raster)
        self.disconnect_all.clicked.connect(self.DisconnectAll)
        
        self.print_timer = QtCore.QTimer(self, interval = 1, timeout = self.print_location)
        self.print_timer.start()
        
    def print_location(self):
        '''
        Prints relative and absolute stage position onto gui. Also enables and disables
        the single shot button.
        '''
        coord = self.NEMA.get_coord()
        home = self.NEMA.get_home()
        rel = str(coord[0] - home[0]) + ", " + str(coord[1] - home[1])
        self.rel_location_lbl.setText(rel)
        self.abs_location_lbl.setText(str(coord[0]) + ", " + str(coord[1]))
        
        if not self.messages_lbl.text() and self.sample_height_txt.text() and self.sample_width_txt.text() \
                and self.step_length_txt.text() and self.num_shots_txt.text() and self.SaveData_dir.toPlainText() \
                and self.rel_location_lbl.text() == "0.0, 0.0":
            try:
                self.spec.set_vals()
                self.Start.setEnabled(True)
            except:
                self.Start.setEnabled(False)
            return
        self.Start.setEnabled(False)

        
    def start_raster(self):
        '''
        Initializes stage location and spectrometer values. Starts the timer for rastering/"single shot". 
        '''
        self.spec.set_vals()
        
        self.NEMA.manual("up", self.NEMA.get_step_length()/2)
        self.NEMA.manual("left", self.NEMA.get_step_length()/2)
        
        self.intigration_time_thor = int(self.thorlabs_inti_time.toPlainText())
        self.inttime = int(self.stellarNet_inti_time.toPlainText())
        
        self.rows = 0
        self.step_count = 1
        self.NEMA.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)
        
        # TODO: FIX
        if self.rate_txt.text():
            self.timer = QtCore.QTimer(self, interval = self.rate_txt.text(), timeout = self.MySpectrometers)
        else:
            self.timer = QtCore.QTimer(self, interval = self.NEMA.get_step_length()*100, timeout = self.MySpectrometers)
        self.timer.start()
        
    def MySpectrometers(self):
        # Calling hardware threads   
        ThorlabsTrigThread = threading.Thread(target=ThorlabsTriggerThread, args=(self.intigration_time_thor, ))
        StellerNetTrigThread = threading.Thread(target=StellerNetTriggerThread, args=(self.inttime, ))
        Fire = threading.Thread(target=FireThread, args=(10, self.dg, ))

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
        hdf.attrs['AbsoluteStageLocation'] = self.NEMA.get_coord()
        hdf.attrs['OtherNotes'] = self.Other_Notes
        hdf.close()
            
        self.file_num += 1
        
        if self.step_count == self.NEMA.get_num_shots():
            self.end_raster()
            return
            
        if self.step_count % self.NEMA.get_max_cols() == 0:
            self.NEMA.manual("up", self.NEMA.get_step_length())
            self.rows += 1
        elif self.rows % 2 == 0:
            self.NEMA.manual("left", self.NEMA.get_step_length())
        elif self.rows % 2 != 0:
            self.NEMA.manual("right", self.NEMA.get_step_length())
     
        self.step_count += 1
        self.NEMA.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)

    def end_raster(self):
        '''
        Stops and deletes timer.
        '''
        self.NEMA.print_location()
        message = "number of Shots Taken: " + str(self.step_count)
        self.messages_lbl.setText(message)
        
        self.spec.clear_vals()
        
        self.timer.stop()
        self.step_count = 1
        del self.timer
    
    def DisconnectAll(self):
        self.dg.disconnect()
        spec.close() # close thorlabs
        self.spec.reset(spectrometer) # close stellarNet

    def closeEvent(self, event):
        '''
        Saves gui input values to json file before closing.
        '''
        try:
            self.end_raster()
        except:
            pass
        
        self.print_timer.stop()
        del self.print_timer
        
        self.dg.write_json()
        self.NEMA.write_json()
        # self.spec.write_json()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    app.exec_()
