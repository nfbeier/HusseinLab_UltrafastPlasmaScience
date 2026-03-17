#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 16:21:51 2025

@author: christina strilets

Delay Generator + FLIR Camera Controller GUI.
Controls the DG645 delay generator and a FLIR Blackfly S USB3 camera.
The delay generator can trigger the camera in hardware trigger mode.
"""

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import instruments as ik
import json
import time, sys
import numpy as np
from time import sleep
from delay_gen_w_cam import Ui_MainWindow
import os
import cv2

# Makes sure you are in the right path!
cwd = os.getcwd()
if "HusseinLab_UltrafastPlasmaScience" not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")
# Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience', prevent import errors
cwd = os.path.sep.join(
    cwd.split(os.path.sep)[: cwd.split(os.path.sep).index("HusseinLab_UltrafastPlasmaScience") + 1]
)
os.chdir(cwd)
sys.path.insert(0, cwd)

from Hardware.DG645.dg645 import DelayGen

# Add the FLIR Camera Code directory to path so we can import it
flir_code_dir = os.path.join(
    cwd, "Software", "SolidTargetStage", "Camera Testing", "FLIR Camera Code"
)
sys.path.insert(0, flir_code_dir)
from blackfly_camera import BlackflyCamera

#%%
class delay_gen_app(QtWidgets.QMainWindow):
    def __init__(self):
        super(delay_gen_app,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    
        #Connecting the instrument
        self.ins_dg = DelayGen("COM4", 9600) # dg645
        
        # Reads in previous input for different channel levels 
        self.read_json()
        
        # Set the saved trigger source on the device
        self.ins_dg.get_trg_src(self.saved_trig_src)
        self.ins_dg.set_trg_src()
        
        # Query and display the current trigger source to confirm
        current_trig_src = self.ins_dg.query_trg_src()
        self.ui.trig_src_disp.setText(current_trig_src)
        
        # Creating the user inputs / buttons for the gui 
        self.ui.delay_select.currentIndexChanged.connect(lambda: self.disp_ch("delay"))
        self.ui.voltage_select.currentIndexChanged.connect(lambda: self.disp_ch("voltage"))
         
        #Adjusting and updating the delay values 
        self.ui.delay_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Val"))
        self.ui.unit_disp.textChanged.connect(lambda: self.updateDelayvals("Delay_Units"))
        
        #Adjusting and updating the voltage values
        self.ui.offset_v.textChanged.connect(lambda: self.updateVoltvals("Offset_Val"))
        self.ui.amplitude_v.textChanged.connect(lambda: self.updateVoltvals("Amp_Val"))
        
        #Selecting the trigger source 
        self.ui.trigger_source_select.currentIndexChanged.connect(self.trg_src_change)
        #Changing the trigger source 
        self.ui.set_trig_src_bt.clicked.connect(self.SetTrigSrc)
        
        
        # Loading and setting the previosuly saved file
        self.ui.set_json_bt.clicked.connect(self.SetSavedBt)
        
        # Setting the delay values 
        self.ui.set_delay_bt.clicked.connect(self.SetDelayBt)
        
        # Setting the voltage values 
        self.ui.set_level_bt.clicked.connect(self.SetVoltageBt)
        
        #Buttons to fire and shutdown
        self.ui.stop_dg_bt.clicked.connect(self.DisconnectBtn)
        
        self.ui.star_dg_bt.clicked.connect(self.FireBtn)
        
        # #Buttons for displaying on the delay generator
        self.ui.T0_bt.clicked.connect(lambda: self.change_display_bt("T0"))
        self.ui.T1_bt.clicked.connect(lambda: self.change_display_bt("T1"))
        self.ui.A_bt.clicked.connect(lambda: self.change_display_bt("A"))
        self.ui.B_bt.clicked.connect(lambda: self.change_display_bt("B"))
        self.ui.C_bt.clicked.connect(lambda: self.change_display_bt("C"))
        self.ui.D_bt.clicked.connect(lambda: self.change_display_bt("D"))
        self.ui.E_bt.clicked.connect(lambda: self.change_display_bt("E"))
        self.ui.F_bt.clicked.connect(lambda: self.change_display_bt("F"))
        self.ui.G_bt.clicked.connect(lambda: self.change_display_bt("G"))
        self.ui.H_bt.clicked.connect(lambda: self.change_display_bt("H"))
        
        # =====================================================================
        #  Camera Setup
        # =====================================================================
        self.cam = BlackflyCamera()
        self.cam_connected = False
        self.video_running = False
        self.last_saved_image = None
        self.image_counter = 0
        
        # Set up the video feed timer
        self.video_timer = QtCore.QTimer(self)
        self.video_timer.timeout.connect(self.update_video_feed)
        
        # Connect camera buttons
        self.ui.FindButton.clicked.connect(self.find_cameras_btn)
        self.ui.ConnectButton.clicked.connect(self.connect_camera)
        self.ui.StartVideoButton.clicked.connect(self.start_video)
        self.ui.StopVideoButton.clicked.connect(self.stop_video)
        self.ui.DisconnectButton.clicked.connect(self.disconnect_camera)
        self.ui.ModeComboBox.currentIndexChanged.connect(self.change_camera_mode)

    # ==================================================================
    #  Delay Generator Methods (unchanged)
    # ==================================================================
    
    #Reads in the json file
    def read_json(self):
        with open("Software\\SolidTargetStage\\SolidTargetDelayGenerator\\delay_gen_gui_inputs.json", "r") as read_file:
            inputs = json.load(read_file)
            print(inputs)
        self.dg_values = {
            "A" : [inputs["A_ch"], inputs["A_delay"], inputs["A_delay_unit"]],
            "B" : [inputs["B_ch"], inputs["B_delay"], inputs["B_delay_unit"]],
            "C" : [inputs["C_ch"], inputs["C_delay"], inputs["C_delay_unit"]],
            "D" : [inputs["D_ch"], inputs["D_delay"], inputs["D_delay_unit"]],
            "E" : [inputs["E_ch"], inputs["E_delay"], inputs["E_delay_unit"]],
            "F" : [inputs["F_ch"], inputs["F_delay"], inputs["F_delay_unit"]],
            "G" : [inputs["G_ch"], inputs["G_delay"], inputs["G_delay_unit"]],
            "H" : [inputs["H_ch"], inputs["H_delay"], inputs["H_delay_unit"]],
            "AB" : [inputs["AB_offset"], inputs["AB_Amp"]], 
            "CD" : [inputs["CD_offset"], inputs["CD_Amp"]], 
            "EF" : [inputs["EF_offset"], inputs["EF_Amp"]],
            "GH" : [inputs["GH_offset"], inputs["GH_Amp"]]
            }
        # Read trigger source if it exists in the JSON file
        self.saved_trig_src = inputs.get("trigger_source", "Internal")
        
    def disp_ch(self, widget):    
        if widget == "delay":
            channel = self.ui.delay_select.currentText()
            self.ui.channel_link.setText(self.dg_values[channel][0])
            self.ui.delay_disp.setText(str(self.dg_values[channel][1]))   
            self.ui.unit_disp.setText(self.dg_values[channel][2])
            
            channel_select =  str(self.ui.delay_select.currentText())
            channel = str(self.ui.channel_link.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.unit_disp.text())
            self.ins_dg.get_delay(channel_select, channel, delay, delay_units)
            
            
            
        elif widget == "voltage":
            channel = self.ui.voltage_select.currentText()
            self.ui.offset_v.setText(str(self.dg_values[channel][0]))
            self.ui.amplitude_v.setText(str(self.dg_values[channel][1]))
            
            voltage_select = str(self.ui.voltage_select.currentText())
            offset_v = float(self.ui.offset_v.text())
            amplitude_v = float(self.ui.amplitude_v.text())
            self.ins_dg.get_voltage(voltage_select, offset_v, amplitude_v)
    
    
    def updateDelayvals(self, widget):
        channel = self.ui.delay_select.currentText()
        self.ui.channel_link.setText(self.dg_values[channel][0])      
        if widget == "Delay_Val" and (self.ui.delay_disp.text() != ''):
            delay = float(self.ui.delay_disp.text())
            self.dg_values[channel][1] = delay
        elif widget == "Delay_Units" and (self.ui.unit_disp.text() != ''):
            delay_units = str(self.ui.unit_disp.text())
            self.dg_values[channel][2] = delay_units
         
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.unit_disp.text() != "":
            channel_select =  str(self.ui.delay_select.currentText())
            channel = str(self.ui.channel_link.text())
            delay = float(self.ui.delay_disp.text())
            delay_units = str(self.ui.unit_disp.text())
            self.ins_dg.get_delay(channel_select, channel, delay, delay_units)
            
            
    def updateVoltvals(self, widget):
        channel = self.ui.voltage_select.currentText()
        if widget == "Offset_Val" and (self.ui.offset_v.text() != ''):
            offset_val = float(self.ui.offset_v.text())
            self.dg_values[channel][0] = offset_val
        elif widget == "Amp_Val" and (self.ui.amplitude_v.text() != ''):
            amp_val = float(self.ui.amplitude_v.text())
            self.dg_values[channel][1] = amp_val
        
        if self.ui.offset_v.text() != "" and self.ui.amplitude_v.text() != "":
            voltage_select = str(self.ui.voltage_select.currentText())
            offset_v = float(self.ui.offset_v.text())
            amplitude_v = float(self.ui.amplitude_v.text())
            self.ins_dg.get_voltage(voltage_select, offset_v, amplitude_v)
    
    def trg_src_change(self):
        
        trg_src = str(self.ui.trigger_source_select.currentText())
        self.ins_dg.get_trg_src(trg_src)
    
    def SetTrigSrc(self):
        # Sets the value in case there was a change
        trg_src = str(self.ui.trigger_source_select.currentText())
        self.ins_dg.get_trg_src(trg_src)
        
        #Now setting the trigger source  
        self.ins_dg.set_trg_src()
        
        #Displaying this value
        current_trig_src = self.ins_dg.query_trg_src()
        self.ui.trig_src_disp.setText(current_trig_src)
        

    def change_display_bt(self, btn):
        
        self.ins_dg.change_display(btn)

    
    def SetSavedBt(self):
        # Sets the saved json values
        i = 0
        for a in self.dg_values:
            if i < 0:
            
                channel = a
                channel_ref = self.dg_values[a][0]
                print(channel,channel_ref)
                delay = self.dg_values[a][1]
                delay_units = self.dg_values[a][2]
                #Get the delay
                self.ins_dg.get_delay(channel, channel_ref, delay, delay_units)
                #Confirm the link
                self.ins_dg.change_delay_link(channel, channel_ref)
                sleep(0.2)
                #Set the delay
                self.ins_dg.set_delay()
                
            elif i > 8:
                voltage_select = str(a)
                offset_v = float(self.dg_values[a][0])
                amplitude_v = float(self.dg_values[a][1])
                self.ins_dg.get_voltage(voltage_select, offset_v, amplitude_v)
                self.ins_dg.set_voltage()
            i = i+1

    
    def SetDelayBt(self):
        # Sets the value
        channel =  str(self.ui.delay_select.currentText())
        channel_ref = str(self.ui.channel_link.text())
        
        #set the new channel link in case there was a change 
        self.ins_dg.change_delay_link(channel, channel_ref)
        
        #Now setting the delay
        sleep(0.2)
        if self.ui.channel_link.text() != "" and self.ui.delay_disp.text() != "" and self.ui.unit_disp.text() != "":
            self.ins_dg.set_delay()
        
            #Then displays the change on the delay generator
            sleep(0.2)      
            self.ins_dg.change_display(channel)
        
        
    def SetVoltageBt(self):
        # Sets the value
        voltage_select = str(self.ui.voltage_select.currentText())
 
        sleep(0.2)
        if self.ui.offset_v.text() != "" and self.ui.amplitude_v.text() != "":
            self.ins_dg.set_voltage()
            #Then displays the change on the delay generator
            sleep(0.2)      
            self.ins_dg.display_amplitdue(voltage_select)
        
              
    def DisconnectBtn(self):
        # First writing the json file to save current settings
        with open("Software\\SolidTargetStage\\SolidTargetDelayGenerator\\delay_gen_gui_inputs.json", "r+") as write_file:
            inputs = json.load(write_file)

            for i in ["A", "B", "C", "D", "E", "F", "G", "H"]:
                inputs[i+"_ch"] = self.dg_values[i][0]
                inputs[i+"_delay"] = self.dg_values[i][1]
                inputs[i+"_delay_unit"] = self.dg_values[i][2]
            for i in ["AB", "CD", "EF", "GH"]:
                inputs[i+"_offset"] = self.dg_values[i][0]
                inputs[i+"_Amp"] = self.dg_values[i][1]

            # Save the current trigger source
            current_trig_src = self.ins_dg.query_trg_src()
            inputs["trigger_source"] = current_trig_src
                
            write_file.seek(0)
            json.dump(inputs, write_file)
            write_file.truncate()
        #Disconnecting the device now
        self.ins_dg.disconnect_dg()
    
    
    def FireBtn(self):
        self.ins_dg.single_shot_fire_dg()
        
        # If camera is connected and in hardware trigger mode, 
        # capture the triggered image
        if self.cam_connected and self.cam.trigger_mode == "hardware":
            if self.cam.is_acquiring:
                image = self.cam.capture_triggered_image(timeout_ms=5000)
                if image is not None:
                    self.last_saved_image = image
                    self.image_counter += 1
                    self.display_image(image, self.ui.SavedImage)
                    print(f"Captured triggered image #{self.image_counter}")
                else:
                    print("Failed to capture triggered image.")
    
    # ==================================================================
    #  Camera Methods
    # ==================================================================
    
    def find_cameras_btn(self):
        """Find available FLIR cameras and populate the combo box."""
        try:
            serials = self.cam.find_cameras()
            if not serials:
                print("No FLIR cameras found.")
                return
            
            # Populate the combo box with found camera serial numbers
            self.ui.Found_Cam_ComboBox.clear()
            for serial in serials:
                self.ui.Found_Cam_ComboBox.addItem(serial)
            
            print(f"Found {len(serials)} camera(s): {serials}")
            
        except Exception as e:
            print(f"Error finding cameras: {e}")
    
    def connect_camera(self):
        """Connect to the camera selected in the Found_Cam_ComboBox."""
        selected_serial = self.ui.Found_Cam_ComboBox.currentText()
        if not selected_serial:
            print("No camera selected. Click 'Find' first.")
            return
        
        try:
            # Disconnect existing camera if one is already connected
            if self.cam_connected:
                self.disconnect_camera()
            
            self.cam.connect(selected_serial)
            self.cam_connected = True
            
            # Apply the current mode selection
            self.change_camera_mode()
            
            print(f"Camera connected: {selected_serial}")
            
        except Exception as e:
            print(f"Error connecting to camera: {e}")
    
    def start_video(self):
        """Start the live video feed."""
        if not self.cam_connected:
            print("No camera connected.")
            return
        
        # Make sure we're in continuous mode for live view
        if self.cam.trigger_mode != "continuous":
            self.cam.configure_continuous()
            self.ui.ModeComboBox.setCurrentIndex(0)  # Set combo to "Continuous"
        
        self.cam.start_acquisition()
        self.video_running = True
        self.video_timer.start(33)  # ~30 fps update rate
        print("Live video started.")
    
    def stop_video(self):
        """Stop the live video feed."""
        self.video_running = False
        self.video_timer.stop()
        
        if self.cam_connected and self.cam.is_acquiring:
            self.cam.stop_acquisition()
        
        print("Live video stopped.")
    
    def update_video_feed(self):
        """Timer callback: grab a frame and display it in the LiveFeedLabel."""
        if not self.cam_connected or not self.video_running:
            return
        
        image = self.cam.get_image(timeout_ms=1000)
        if image is not None:
            self.display_image(image, self.ui.LiveFeedLabel)
    
    def change_camera_mode(self):
        """Handle camera mode change from the ModeComboBox."""
        if not self.cam_connected:
            return
        
        # Stop video if running before changing mode
        if self.video_running:
            self.stop_video()
        
        mode = self.ui.ModeComboBox.currentText().strip()
        
        if mode == "Continous" or mode == "Continuous":
            self.cam.configure_continuous()
        elif mode == "Hardware Trigger":
            self.cam.configure_trigger(source="hardware")
            # Start acquisition so camera is armed and waiting for trigger
            self.cam.start_acquisition()
            print("Camera armed for hardware trigger. Fire the delay generator to capture.")
    
    def disconnect_camera(self):
        """Disconnect the camera and clean up."""
        if self.video_running:
            self.stop_video()
        
        if self.cam_connected:
            self.cam.disconnect()
            self.cam_connected = False
            print("Camera disconnected.")
    
    def display_image(self, image_array, label_widget):
        """
        Display a numpy image array on a QLabel widget.
        
        Parameters
        ----------
        image_array : numpy.ndarray
            The image to display (grayscale or color).
        label_widget : QLabel
            The QLabel to display the image on.
        """
        # Resize to fit the label
        label_width = label_widget.width()
        label_height = label_widget.height()
        image_resized = cv2.resize(image_array, (label_width, label_height))
        
        if len(image_resized.shape) == 2:
            # Grayscale image
            height, width = image_resized.shape
            bytes_per_line = width
            q_img = QtGui.QImage(
                image_resized.data, width, height, 
                bytes_per_line, QtGui.QImage.Format_Grayscale8
            )
        else:
            # Color image
            height, width, channels = image_resized.shape
            bytes_per_line = channels * width
            q_img = QtGui.QImage(
                image_resized.data, width, height, 
                bytes_per_line, QtGui.QImage.Format_RGB888
            ).rgbSwapped()
        
        label_widget.setPixmap(QtGui.QPixmap.fromImage(q_img))
    
    def save_image(self, image_array, filepath):
        """
        Save a numpy image array to a file.
        
        Parameters
        ----------
        image_array : numpy.ndarray
            The image to save.
        filepath : str
            Path to save the image to (e.g., 'capture_001.png').
        """
        cv2.imwrite(filepath, image_array)
        print(f"Image saved to {filepath}")
    
    # ==================================================================
    #  Window Close Event
    # ==================================================================
    def closeEvent(self, event):
        """Clean up camera resources when the window is closed."""
        if self.video_running:
            self.stop_video()
        if self.cam_connected:
            self.cam.disconnect()
        self.cam.release_system()
        event.accept()
    

if __name__ == "__main__":
    #from ResultsWindow import Results
    app = QtWidgets.QApplication(sys.argv)
    application = delay_gen_app()
    application.show()
    sys.exit(app.exec_()) 
# %%
