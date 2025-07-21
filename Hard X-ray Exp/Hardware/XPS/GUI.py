# Ying Wan, Shubho Mohajan, Dr. Nick Beier, Dr. Amina Hussein

from PyQt5 import QtWidgets, uic, QtGui, QtCore
from XPS import XPS
from math import floor
from fractions import Fraction
import sys, time, json

#GUI Design file importing here (qt design file)
qtcreator_file  = 'GUI.ui' # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    '''
    Connects all GUI elements to methods of controlling the XPS. 
    '''
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
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
        self.stop_btn.clicked.connect(self.end_timer)
        
        # Timer and Printing of Stage Location
        self.print_timer = QtCore.QTimer(self, interval = 1000, timeout = self.print_location)
        self.print_timer.start()
        self.print_location()
        
        self.read_json()
        
    def read_json(self):
        '''
        Reads the .json file and auto-fills the GUI with inputs from last use.
        '''
        with open("gui_inputs.json", "r") as read_file:
            inputs = json.load(read_file)
            
        for widget in self.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(inputs[str(widget.objectName())])
        
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
                
            for widget in self.children():
                if not isinstance(widget, (QtCore.QTimer, QtGui.QDoubleValidator, QtGui.QIntValidator)):
                    widget.setEnabled(False)
            self.initialize_btn.setEnabled(True)
            self.messages.setText("Not Initialized")

        elif stage_status == "Disabled state":
            for widget in self.children():
                if not isinstance(widget, (QtCore.QTimer, QtGui.QDoubleValidator, QtGui.QIntValidator)):
                    widget.setEnabled(False)
            self.enable_btn.setEnabled(True)
            self.enable_btn.setText("Enable")

        # Initialized and enabled
        elif stage_status[:11].upper() == "Ready state".upper():
            for widget in self.children():
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
            self.sample_length = self.x_xps.getStagePosition(self.x_axis) - self.ref[0]
            self.sample_length_line.setText(str(self.sample_length))
        elif inp == 'set_bound_y':
            self.sample_width = self.y_xps.getStagePosition(self.y_axis) - self.ref[1]
            self.sample_width_line.setText(str(self.sample_width))
        elif inp == 'num_shots':
            if self.num_shots_line.text():
                self.num_shots = int(self.num_shots_line.text())
            if self.step_length_line.text() and self.sample_length_line.text() \
                and self.sample_width_line.text() and not self.messages.text():
                self.raster_btn.setEnabled(True)
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
        self.x_xps.moveAbsolute(self.x_axis, self.ref[0] + self.step_length/2)
        self.y_xps.moveAbsolute(self.y_axis, self.ref[1] + self.step_length/2)
        self.step_count = 1
        self.rows = 0
        
        self.print_location()
        msg = 'number of steps taken: ' + str(self.step_count)
        self.messages.setText(msg)
        
        if self.rep_rate_line.text():
            rep_rate = int(float(self.rep_rate_line.text()) * 1000)
        else: 
            rep_rate = 0
        
        self.rast_timer = QtCore.QTimer(self, interval = rep_rate, timeout = self.raster)
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
        
    def write_json(self):
        '''
        Writes gui inputs to .json file to load for next use.
        '''
        with open("gui_inputs.json", "r+") as write_file:
            inputs = json.load(write_file)
            
            for widget in self.children():
                if isinstance(widget, QtWidgets.QLineEdit):
                    inputs[str(widget.objectName())] = widget.text()
                
            write_file.seek(0)
            json.dump(inputs, write_file)
            write_file.truncate
        
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
        QtWidgets.QApplication.quit() 
        event.accept()
        
            
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()

    sys.exit(app.exec_())
