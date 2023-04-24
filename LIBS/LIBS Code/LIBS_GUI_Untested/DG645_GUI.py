from PyQt5 import QtWidgets, uic, QtGui, QtCore
import instruments as ik
import quantities as pq
import json

class DelayGenerator:
    def __init__(self, ui):
        self.ui = ui
        self.ins = ik.srs.SRSDG645.open_serial("COM12", 9600) # dg645
        
        self.read_json()
        self.edit_ch("delay")
        self.edit_ch("voltage")
        
    def read_json(self):
        with open("gui_inputs.json", "r") as read_file:
            inputs = json.load(read_file)
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
                    
    def edit_ch(self, widget):
        if widget == "delay":
            channel = self.ui.delay_combo.currentText()
            self.ui.channel_line.setText(self.dg_values[channel][0])
            self.ui.delay_line.setText(str(self.dg_values[channel][1]))
            self.ui.unit_line.setText(self.dg_values[channel][2])
            self.set_delay()
        elif widget == "voltage":
            channel = self.ui.voltage_combo.currentText()
            self.ui.offset_line.setText(str(self.dg_values[channel][0]))
            self.ui.amplitude_line.setText(str(self.dg_values[channel][1]))
            self.set_voltage()
        
    def edit_val(self, widget):    
        delay_ch = self.ui.delay_combo.currentText()
        voltage_ch = self.ui.voltage_combo.currentText()
        
        if widget == "channel":
            self.dg_values[delay_ch][0] = self.ui.channel_line.text()
        elif widget == "delay":
            if self.ui.delay_line.text() != "":
                self.dg_values[delay_ch][1] = float(self.ui.delay_line.text())
        elif widget == "unit":
            self.dg_values[delay_ch][2] = self.ui.unit_line.text()
        elif widget == "offset":
            if self.ui.offset_line.text() != "":
                self.dg_values[voltage_ch][0] = float(self.ui.offset_line.text())
        elif widget == "amplitude":
            if self.ui.amplitude_line.text() != "":
                self.dg_values[voltage_ch][1] = float(self.ui.amplitude_line.text())
        
        if self.ui.channel_line.text() != "" and self.ui.delay_line.text() != "" and self.ui.unit_line.text() != "":
            self.set_delay()
        
        if self.ui.offset_line.text() != "" and self.ui.amplitude_line.text() != "":
            self.set_voltage()
            
    def change_display(self, btn):
        cmd = {
            "T0" : "DISP 11,0",
            "T1" : "DISP 11,1",
            "A" : "DISP 11,2",
            "B" : "DISP 11,3",
            "C" : "DISP 11,4",
            "D" : "DISP 11,5",
            "E" : "DISP 11,6",
            "F" : "DISP 11,7",
            "G" : "DISP 11,8",
            "H" : "DISP 11,9"
            }
        self.ins.sendcmd(cmd[btn])
        
    def send_command(self, cmd):
        self.ins.sendcmd(cmd)
        
            
    def set_delay(self):
        try:
            self.ins.channel[self.ui.delay_combo.currentText()].delay = (self.ins.channel[self.ui.channel_line.text()], pq.Quantity(float(self.ui.delay_line.text()), self.ui.unit_line.text()))
            self.ui.message.setText("")
        except:
            self.ui.messages_lbl.setText("ERROR: check channel delay inputs")
            
    def set_voltage(self):
        try:
            self.ins.output[self.ui.voltage_combo.currentText()].level_offset = pq.Quantity(float(self.ui.offset_line.text()), "V")
            self.ins.output[self.ui.voltage_combo.currentText()].level_amplitude = pq.Quantity(float(self.ui.amplitude_line.text()), "V")
            self.ui.message.setText("")
        except:
            self.ui.messages_lbl.setText("ERROR: check channel voltage inputs")
        
    def disconnect(self):
        self.ins.sendcmd("IFRS 0")
        
    def write_json(self):
        with open("gui_inputs.json", "r+") as write_file:
            inputs = json.load(write_file)
            
            for i in ["A", "B", "C", "D", "E", "F", "G", "H"]:
                inputs[i+"_ch"] = self.dg_values[i][0]
                inputs[i+"_delay"] = self.dg_values[i][1]
                inputs[i+"_delay_unit"] = self.dg_values[i][2]
            for i in ["AB", "CD", "EF", "GH"]:
                inputs[i+"_offset"] = self.dg_values[i][0]
                inputs[i+"_Amp"] = self.dg_values[i][1]
                
            write_file.seek(0)
            json.dump(inputs, write_file)
            write_file.truncate()