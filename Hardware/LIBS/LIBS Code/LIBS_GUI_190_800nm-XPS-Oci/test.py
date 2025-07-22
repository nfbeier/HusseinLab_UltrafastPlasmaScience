from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys, threading, h5py
from fractions import Fraction
from XPS import XPS
import json
import pyvisa as visa

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

def wavelengthCalibration(coeffs):
    pixels = np.arange(2048)#.reshape(-1, 1)
    wave = coeffs[2]+coeffs[0]*pixels/2+coeffs[1]*(pixels/2)**2+coeffs[3]*(pixels/2)**3
    return wave

ins = ik.srs.SRSDG645.open_serial('COM8', 9600) # dg645
spectrometerIDs = {'23020204':1,'23092809':3,'23092819':4,'23092829':5}
devices = sn.find_devices()
print(devices)
devices = [i for i in devices]
print(devices)
# print(devices[0].get_config()['coeffs'])
spectrometers, waves = [0,0,0,0,0,0], [0,0,0,0,0,0]
for key,elem in spectrometerIDs.items():
    for count,device in enumerate(devices):
        if device.get_device_id() == key:
            spectrometers[elem] = device
            coeffs = device.get_config()['coeffs']
            waves[elem] = wavelengthCalibration(coeffs)
            devices.pop(count)
            
print(devices)    
# if devices[0].get_config()['coeffs'][2] < devices[1].get_config()['coeffs'][2]:      
#     print('woohoo')
# else:
#     print(spectrometerIDs.items())
# if devices[0].get_config()['coeffs'][2] < devices[1].get_config()['coeffs'][2]:
#     spectrometers[0] = devices[0]
#     waves[0] = wavelengthCalibration(devices[0].get_config()['coeffs'])
#     spectrometers[2] = devices[1]
#     waves[2] = wavelengthCalibration(devices[1].get_config()['coeffs'])
# else:
#     spectrometers[2] = devices[0]
#     waves[2] = wavelengthCalibration(devices[0].get_config()['coeffs'])
#     spectrometers[0] = devices[1]
#     waves[0] = wavelengthCalibration(devices[1].get_config()['coeffs'])

# print(devices)
# print(devices[1].get_config()['coeffs'])