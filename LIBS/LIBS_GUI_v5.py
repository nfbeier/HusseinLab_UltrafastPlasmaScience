# LIBS GUI v5, 2022-06-03
# Shubho Mohajan, Dr. Nicholas Beier, Dr. Amina Hussein
# University of Alberta, ECE Department

from PyQt5 import QtWidgets, uic, QtGui, QtCore
from pyqtgraph import PlotWidget
import pyqtgraph as pg
import sys
import threading
import h5py

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k') 

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
import time
import numpy as np
# import the usb driver
import stellarnet_driver3 as sn
import matplotlib.pyplot as plt
import logging
logging.basicConfig(format='%(asctime)s %(message)s')



#GUI Design file importing here (qt design file)
qtcreator_file  = "LIBS_GUI_v5.ui" # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

#Connecting all hardwares
ins = ik.srs.SRSDG645.open_serial('COM3', 9600) # dg645
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
        self.Start.clicked.connect(self.MySpectrometers)
        self.Start.clicked.connect(self.CountNum)
        self.disconnect_all.clicked.connect(self.DisconnectAll)
        self._submit_counter = 0
        
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
        
    def CountNum(self):
        self._submit_counter += 1
    
    def MetaData(self):
        self.LaserEnergy = float(self.LaserEnergy.toPlainText())
        self.LaserWavelength = float(self.LaserWavelength.toPlainText())
        self.LaserPulseDuration = float(self.LaserPulseDuration.toPlainText())
        self.SampleType = self.SampleType.toPlainText()
        self.FocalLength = float(self.FocalLength.toPlainText())
        self.IntegrationTime = float(self.IntegrationTime.toPlainText())
        self.FiberAngle = float(self.FiberAngle.toPlainText())
        self.BackgroundSpectrum = self.BackgroundSpectrum.toPlainText()
        self.OtherNotes = self.OtherNotes.toPlainText()

        
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
        
    
    def MySpectrometers(self):
        
        # Setting Intigration Time
        intigration_time_thor = int(self.thorlabs_inti_time.toPlainText())
        inttime = int(self.stellarNet_inti_time.toPlainText())
        
        # Calling hardware threads        
        ThorlabsTrigThread = threading.Thread(target=ThorlabsTriggerThread, args=(intigration_time_thor, ))
        StellerNetTrigThread = threading.Thread(target=StellerNetTriggerThread, args=(inttime, ))
        Fire =  threading.Thread(target=FireThread, args=(10, ))

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
        txtnum = self._submit_counter
        path_SaveData = self.SaveData_dir.toPlainText()
        hdf = h5py.File (path_SaveData + '/'  + time.strftime("%Y%m%d")+'_LIBS_Spectrum_{}.h5'.format(txtnum), 'w')
        ThorlabsSpectrum = hdf.create_dataset('ThorlabsSpectrum', data=data_thor_zip)
        StellarNetSpectrum = hdf.create_dataset('StellarNetSpectrum', data=data_stellar)
        ThorlabsSpectrum.attrs['LaserEnergy'] = self.LaserEnergy
        ThorlabsSpectrum.attrs['LaserWavelength'] = self.LaserWavelength
        ThorlabsSpectrum.attrs['LaserPulseDuration'] = self.LaserPulseDuration
        ThorlabsSpectrum.attrs['SampleType'] = self.SampleType
        ThorlabsSpectrum.attrs['FocalLength'] = self.FocalLength
        ThorlabsSpectrum.attrs['IntegrationTime'] = self.IntegrationTime
        ThorlabsSpectrum.attrs['FiberAngle'] = self.FiberAngle
        ThorlabsSpectrum.attrs['BackgroundSpectrum'] = self.BackgroundSpectrum
        ThorlabsSpectrum.attrs['OtherNotes'] = self.OtherNotes
        StellarNetSpectrum.attrs['LaserEnergy'] = self.LaserEnergy
        StellarNetSpectrum.attrs['LaserWavelength'] = self.LaserWavelength
        StellarNetSpectrum.attrs['LaserPulseDuration'] = self.LaserPulseDuration
        StellarNetSpectrum.attrs['SampleType'] = self.SampleType
        StellarNetSpectrum.attrs['FocalLength'] = self.FocalLength
        StellarNetSpectrum.attrs['IntegrationTime'] = self.IntegrationTime
        StellarNetSpectrum.attrs['FiberAngle'] = self.FiberAngle
        StellarNetSpectrum.attrs['BackgroundSpectrum'] = self.BackgroundSpectrum
        StellarNetSpectrum.attrs['OtherNotes'] = self.OtherNotes
        hdf.close()

        time.sleep(1)


    def reset(self, spectrometer):
        spectrometer['device'].__del__()
    
    def DisconnectAll(self):
        ins.sendcmd('IFRS 0') #close dg 645
        spec.close() # close thorlabs
        self.reset(spectrometer) # close stellarNet
        


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
