# -*- coding: utf-8 -*-
"""
Created on Fri May  6 15:18:50 2022

@author: Hussein-Lab
"""

import sys
# To use this, we need to install the thorlabs OSA software and driver in pc
sys.path.append(r"C:\Users\R2D2\Documents\CODE\Github\HusseinLab_UltrafastPlasmaScience\Hardware\Thorlabs CCS200")

#This is to ignore pyvisa and instruments-lib warnings
import warnings
warnings.filterwarnings('ignore')

import pyvisa
from instrumental import instrument, list_instruments
from instrumental.drivers.spectrometers import thorlabs_ccs
import matplotlib.pyplot as plt

rm = pyvisa.ResourceManager()

print(rm)

res = rm.list_resources('?*::?*')

print(res)

#%%

paramsets = list_instruments()

print(paramsets)

#%%
spec = instrument(paramsets[0],reopen_policy = "new")
print(spec)

#%%
print(spec.get_integration_time())

spec.set_integration_time('100 ms')
print(spec.get_integration_time())
#%%
spec.start_single_scan()
data = spec.get_scan_data()
#%%
plt.plot(data)
#%%
=======
class ThorlabsCCS:
    def __init__(self):
        rm = pyvisa.ResourceManager()   
        res = rm.list_resources('?*::?*')
        paramsets = list_instruments()
        
        if res:
            print(True)
        #print(rm)
        #print(res)
        
        self.spec = instrument(paramsets[0],reopen_policy = "new")
    
    def close(self):
        self.spec.close()
        
    def __del__(self):
        try:
            self.spec.close()   
        except ThorlabsCCSError:  
            print("Thorlabs Spectrometer could not be closed. Check connection.")
            
if __name__ == "__main__":
    thor = ThorlabsCCS()
