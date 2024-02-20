import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, MaxNLocator
import numpy as np
file = r'Hardware\pyFROG\Old Examples\data\frg_trace_1580511001.pkl'

data = pd.read_pickle(file)

#plt.plot(data['wave'],data['trace'])
wave = data['wave'][0]
trace = data['trace'][0].T

# Define the locations for the axes
left, width = 0.12, 0.55
bottom, height = 0.12, 0.55
bottom_h = left_h = left+width+0.02
 
# Set up the geometry of the three plots
rect_trace = [left, bottom, width, height] # dimensions of temp plot
rect_autocorr = [left, bottom_h, width, 0.25] # dimensions of x-histogram
rect_autoconv = [left_h, bottom, 0.25, height] # dimensions of y-histogram

fig = plt.figure(1, figsize=(7,6))
# Make the three plots
axTrace = plt.axes(rect_trace) # temperature plot
ax_autocorr = plt.axes(rect_autocorr) # x histogram
ax_autoconv = plt.axes(rect_autoconv) # y histogram

# Remove the inner axes numbers of the histograms
nullfmt = NullFormatter()
ax_autocorr.xaxis.set_major_formatter(nullfmt)
ax_autoconv.yaxis.set_major_formatter(nullfmt)

axTrace.imshow(trace,aspect = 'auto',extent = [-50,50,wave[0],wave[-1]],origin='lower')
ax_autoconv.plot(np.sum(trace,axis = 1),wave)
ax_autocorr.plot(np.sum(trace,axis = 0))
#plt.colorbar()
axTrace.set_xlabel("Delay [fs]")
axTrace.set_ylabel("Wavelength [nm]")
ax_autoconv.set_title("Autoconvolution")
ax_autocorr.set_title("Autocorrelation")
plt.tight_layout()
plt.show()