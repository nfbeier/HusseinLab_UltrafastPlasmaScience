import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, MaxNLocator
import numpy as np
from scipy.signal import find_peaks, peak_widths

file_bkg = r'Hardware\pyFROG\Old Examples\data\frg_trace.pkl'
file = r'Hardware\pyFROG\Old Examples\data\frg_trace_1580511001.pkl'

data_bkg = pd.read_pickle(file_bkg)
data = pd.read_pickle(file)

#plt.plot(data['wave'],data['trace'])
wave = data['wave'][0]
trace = data['trace'][0]
trace_bkg = data_bkg['trace'][0]
trace -= trace_bkg

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

timeAxis = np.linspace(-100,100,100)
axTrace.imshow(trace.T,aspect = 'auto',origin = 'lower',extent = [timeAxis[0],timeAxis[-1],wave[0],wave[-1]])
autocorr = np.sum(trace,axis = 1)
autoconv = np.sum(trace,axis = 0)
ax_autoconv.plot(autoconv,wave)
ax_autocorr.plot(timeAxis, autocorr)

peaks,_ = find_peaks(autocorr,distance=100)
results_half = peak_widths(autocorr,peaks,rel_height=0.5)[0]
autocorr_val = results_half[0]*(timeAxis[1]-timeAxis[0])
tempFWHM = autocorr_val/np.sqrt(2)

axTrace.set_xlabel("Delay [fs]")
axTrace.set_ylabel("Wavelength [nm]")
ax_autocorr.set_xlim([-100,100])
ax_autoconv.set_ylim([wave[0],wave[-1]])
ax_autoconv.set_title("Autoconvolution")
ax_autocorr.set_title("Autocorrelation")
peaks,_ = find_peaks(autocorr,distance=100)
results_half = peak_widths(autocorr,peaks,rel_height=0.5)[0]
autocorr_val = results_half[0]*(timeAxis[1]-timeAxis[0])
tempFWHM = autocorr_val/np.sqrt(2)
axTrace.text(1.05, 1.49, f'Autocorrelation: {autocorr_val:.1f} fs\nTemporal FWHM: {tempFWHM:.1f} fs', transform=axTrace.transAxes, fontsize=10,
        verticalalignment='top')
plt.show()