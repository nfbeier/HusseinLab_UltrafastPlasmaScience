# LIBS GUI v5, 2022-06-03
# Ying Wan, Shubho Mohajan, Dr. Nicholas Beier, Dr. Amina Hussein
# University of Alberta, ECE Department

from PyQt5 import QtWidgets, uic, QtGui, QtCore
from stage_control import Motor, Control
from math import floor
from fractions import Fraction
import json, time

class NEMA:
    def __init__(self, ui):
        self.ui = ui
        self.read_json()
        coord, home = self.init_stage_vals()
        self.motor = Motor(coord, home)
        self.control = Control()

        self.ui.manual_step_length_txt.setValidator(QtGui.QDoubleValidator(0.10, 105.00, 2))
        self.ui.sample_height_txt.setValidator(QtGui.QDoubleValidator(0.10, 105.00, 2))
        self.ui.sample_width_txt.setValidator(QtGui.QDoubleValidator(0.10, 105.00, 2))
        self.ui.step_length_txt.setValidator(QtGui.QDoubleValidator(0.10, 105.00, 2))

        self.ui.num_shots_txt.setEnabled(False)
        self.ui.raster_btn.setEnabled(False)

        self.sample_width = float(self.ui.sample_width_txt.text())
        self.sample_height = float(self.ui.sample_height_txt.text())
        self.step_length = float(self.ui.step_length_txt.text())
        self.num_shots = float(self.ui.num_shots_txt.text())
        self.max_cols = floor(Fraction(str(self.sample_width))/Fraction(str(self.step_length)))
        self.max_rows = floor(Fraction(str(self.sample_height))/Fraction(str(self.step_length)))
        self.max_shots = self.max_cols * self.max_rows

    def get_step_length(self):
        return self.step_length

    def get_num_shots(self):
        return self.num_shots

    def get_max_cols(self):
        return self.max_cols
    
    def get_coord(self):
        return self.motor.get_coord()
    
    def get_home(self):
        return self.motor.get_home()
        
    def read_json(self):
        with open("gui_inputs.json", "r") as read_file:
            inputs = json.load(read_file)

        for widget in self.ui.translationStage.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(inputs[str(widget.objectName())]) 
        self.ui.abs_location_lbl.setText(inputs["abs_location_lbl"])
        self.ui.rel_location_lbl.setText(inputs["rel_location_lbl"])

    def init_stage_vals(self):
        '''
        Reads in coordinate and home coordinate of the stage's last usage from gui textboxes.

        Returns
        -------
        coord (float): Absolute coordinate of stage location.
        home (float): Absolute coordinate of home location.
        '''
        abs_x, abs_y = self.ui.abs_location_lbl.text().split(", ")
        rel_x, rel_y = self.ui.rel_location_lbl.text().split(", ")
        
        coord = [float(abs_x), float(abs_y)]
        home = [float(abs_x) - float(rel_x), float(abs_y) - float(rel_y)]
        return coord, home 

    def manual(self, btn, dist):
        '''
        Executes manual controls: moves left, right, up, down, sets home, returns home.
        Also prints errors and absolute and relative locations.
        
        Parameters
        ----------
        btn (string): Button pressed in gui.
        '''
        self.ui.messages_lbl.setText("")
        coord = self.motor.get_coord()
        
        if btn == "left":
            if (coord[0] - dist) >= self.motor.get_min()[0]:
                self.control.right(self.motor, dist)
            else:
                self.ui.messages_lbl.setText("ERROR: reached end stop limit")

        elif btn == "right":
            if (coord[0] + dist) <= self.motor.get_max()[0]:
                self.control.left(self.motor, dist)
            else:
                self.ui.messages_lbl.setText("ERROR: reached end stop limit")

        elif btn == "up":
            if (coord[1] - dist) >= self.motor.get_min()[1]:
                self.control.up(self.motor, dist)
            else:
                self.ui.messages_lbl.setText("ERROR: reached end stop limit")

        elif btn == "down":
            if (coord[1] + dist) <= self.motor.get_max()[1]:
                self.control.down(self.motor, dist)
            else:
                self.ui.messages_lbl.setText("ERROR: reached end stop limit")

        elif btn == "set":
            self.motor.set_home(self.motor.get_coord()[0], self.motor.get_coord()[1])

        elif btn == "return":
            self.control.return_home(self.motor)

    def set_limits(self, btn):
        '''
        Calibrates sample size based on the distance between home and current stage location.

        Parameters:
        -----------
        btn (string): Indicates which button was hit and whether to calibrate the x or y axis
        '''
        if btn == "x":
            self.sample_width = abs(self.motor.get_coord()[0] - self.motor.get_home()[0])
            self.ui.sample_width_txt.setText(str(self.sample_width))
        elif btn == "y":
            self.sample_height = abs(self.motor.get_coord()[1] - self.motor.get_home()[1])
            self.ui.sample_height_txt.setText(str(self.sample_height))

    def raster_inp(self, inp):
        '''
        Takes input for raster controls: takes input for step length and sample length, calculates 
        number of max shots, takes input for number of shots.
        
        Parameters
        ----------
        inp (string): Textbox edited in gui.
        '''
        self.ui.messages_lbl.clear()
        max_width = self.motor.get_max()[0] - abs(self.motor.get_home()[0])
        max_height = self.motor.get_max()[1] - self.motor.get_home()[1]
        
        if inp=="sample width" and self.ui.sample_width_txt.text():
            if float(self.ui.sample_width_txt.text()) > max_width:
                self.ui.messages_lbl.setText("ERROR: sample length exceeds end stops")
                self.ui.sample_width_txt.setText(str(max_width))
            self.sample_width = float(self.ui.sample_width_txt.text())

        elif inp=="sample height" and self.ui.sample_height_txt.text():
            if float(self.ui.sample_height_txt.text()) > max_height:
                self.ui.messages_lbl.setText("ERROR: sample length exceeds end stops")
                self.ui.sample_height_txt.setText(str(self.max_height))
            self.sample_height = float(self.ui.sample_height_txt.text())
                
        elif inp=="step length" and self.ui.step_length_txt.text():
            if float(self.ui.step_length_txt.text()) > max_width:
                self.ui.messages_lbl.setText("ERROR: step length exceeds end stops")
                self.ui.step_length_txt.setText(str(self.max_width))
            elif float(self.ui.step_length_txt.text()) > max_height:
                self.ui.messages_lbl.setText("ERROR: step length exceeds end stops")
                self.ui.step_length_txt.setText(str(self.max_height))
            # Will throw an error later since division by 0 is not allowed 
            elif float(self.ui.step_length_txt.text()) == 0:
                self.ui.messages_lbl.setText("ERROR: step length cannot be 0")
                return
            self.step_length = float(self.ui.step_length_txt.text())

        elif inp == "shots" and self.ui.num_shots_txt.text():
            self.num_shots = int(self.ui.num_shots_txt.text())
            return

        self.ui.num_shots_txt.clear()
        self.ui.raster_btn.setEnabled(False)
        self.ui.num_shots_txt.setEnabled(False)

        # Can only run once both lengths have been inputted, or else gui will crash.
        if self.ui.sample_width_txt.text() and self.ui.step_length_txt.text():
            if self.step_length > self.sample_width:
                self.ui.messages_lbl.setText("ERROR: step length is larger than sample length")
                # Assume step length is equal to sample length.
                self.step_length = self.sample_width
                self.ui.step_length_txt.setText(str(self.step_length))
            # Float division will sometimes floor/round incorrectly without using Fraction.
            self.max_cols = floor(Fraction(str(self.sample_width))/Fraction(str(self.step_length)))
            
        if self.ui.sample_height_txt.text() and self.ui.step_length_txt.text():
            if self.step_length > self.sample_height:
                self.ui.messages_lbl.setText("ERROR: step length is larger than sample length")
                # Assume step length is equal to sample length.
                self.step_length = self.sample_height
                self.ui.step_length_txt.setText(str(self.step_length))
            self.max_rows = floor((Fraction(str(self.sample_height)))/(Fraction(str(self.step_length))))

        if self.ui.sample_height_txt.text() and self.ui.sample_width_txt.text() and self.ui.step_length_txt.text():
            self.max_shots = self.max_cols * self.max_rows
            self.ui.num_shots_txt.setValidator(QtGui.QIntValidator(1, self.max_shots, self.ui))
            self.ui.num_shots_txt.setEnabled(True)

        self.ui.max_lbl.setText(str(self.max_shots))
        
    # def start_test_raster(self, timer):
    #     '''
    #     Initializes stage location and spectrometer values. Starts the timer for testing raster path. 
    #     '''
    #     self.manual("up", self.step_length/2)
    #     self.manual("left", self.step_length/2)
    #     self.rows = 0
    #     self.step_count = 1
    #     self.print_location()
    #     message = "number of Shots Taken: " + str(self.step_count)
    #     self.ui.messages_lbl.setText(message)
        
    #     self.timer = QtCore.QTimer(self, interval = self.step_length/10, timeout = self.test_raster)
    #     self.timer.start()

    # def test_raster(self):
    #     '''
    #     moves stage in raster path without triggering spectrometers and laser. Used for testing.
    #     '''
    #     if self.step_count == self.num_shots:
    #         self.end_raster()
    #         return
        
    #     if self.step_count !=0 and self.step_count % self.max_cols == 0:
    #         self.manual("up", self.step_length)
    #         self.rows += 1
    #     elif self.rows % 2 == 0:
    #         self.manual("left", self.step_length)
    #     elif self.rows % 2 != 0:
    #         self.manual("right", self.step_length)
            
    #     self.step_count += 1
    #     self.print_location()
    #     message = "number of Shots Taken: " + str(self.step_count)
    #     self.ui.messages_lbl.setText(message)
        
    #     time.sleep(1)

    # def end_raster(self, timer):
    #     '''
    #     Stops and deletes timer.
    #     '''
    #     self.print_location()
    #     message = "number of Shots Taken: " + str(self.step_count)
    #     self.messages_lbl.setText(message)
        
    #     timer.stop()
    #     self.step_count = 1
    #     del self.timer

    def write_json(self):
        '''
        Writes values from textboxes and labels on gui to json file.
        '''
        with open("gui_inputs.json", "r+") as write_file:
            inputs = json.load(write_file)

            for widget in self.ui.translationStage.children():
                if isinstance(widget, QtWidgets.QLineEdit):
                    if widget.text() != "":
                        inputs[str(widget.objectName())] = widget.text()
                    else:
                        inputs[str(widget.objectName())] = "1"
                    
            inputs["abs_location_lbl"] = self.ui.abs_location_lbl.text()
            inputs["rel_location_lbl"] = self.ui.rel_location_lbl.text()
                
            write_file.seek(0)
            json.dump(inputs, write_file)
            write_file.truncate()