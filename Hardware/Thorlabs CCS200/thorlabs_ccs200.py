# -*- coding: utf-8 -*-
"""
Created on Fri May  6 15:18:50 2022

@author: Hussein-Lab
"""

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
spec.close()