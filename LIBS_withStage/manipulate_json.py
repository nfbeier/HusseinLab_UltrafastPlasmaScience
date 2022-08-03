from PyQt5 import QtWidgets, uic, QtGui, QtCore
import json

def read_json(ui):
    '''
    Reads json file and auto-fills textboxes and labels on gui from last usage.
    
    Parameters
    ----------
    ui : Instance of the MyApp class from LIBSGUI.py.
    '''
    with open("gui_inputs.json", "r") as read_file:
        inputs = json.load(read_file)
        
    for widget in ui.dg.children():
        if isinstance(widget, QtWidgets.QTextEdit):
            widget.setText(inputs[str(widget.objectName())])
            
    for widget in ui.spectrometers.children():
        if isinstance(widget, QtWidgets.QTextEdit):
            if widget.objectName() != "SaveData_dir":
                widget.setText(inputs[str(widget.objectName())])
                
    for widget in ui.translationStage.children():
        if isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(inputs[str(widget.objectName())])
            
    ui.abs_location_lbl.setText(inputs["abs_location_lbl"])
    ui.rel_location_lbl.setText(inputs["rel_location_lbl"])

def write_json(ui):
    '''
    Writes values from textboxes and labels on gui to json file.
    
    Parameters
    ----------
    ui : Instance of the MyApp class from LIBSGUI.py.
    '''
    with open("gui_inputs.json", "r+") as write_file:
        inputs = json.load(write_file)
        
        for widget in ui.dg.children():
            if isinstance(widget, QtWidgets.QTextEdit):
                inputs[str(widget.objectName())] = widget.toPlainText()
                
        for widget in ui.spectrometers.children():
            if isinstance(widget, QtWidgets.QTextEdit):
                if widget.objectName() != "SaveData_dir":
                    inputs[str(widget.objectName())] = widget.toPlainText()
                    
        for widget in ui.translationStage.children():
            if isinstance(widget, QtWidgets.QLineEdit):
                inputs[str(widget.objectName())] = widget.text()
                
        inputs["abs_location_lbl"] = ui.abs_location_lbl.text()
        inputs["rel_location_lbl"] = ui.rel_location_lbl.text()
            
        write_file.seek(0)
        json.dump(inputs, write_file)
        write_file.truncate()
    
