from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, MaxNLocator
import pandas as pd
import numpy as np

class frogTraceCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        # Define the locations for the axes
        left, width = 0.12, 0.55
        bottom, height = 0.12, 0.55
        bottom_h = left_h = left+width+0.02
        
        # Set up the geometry of the three plots
        rect_trace = [left, bottom, width, height] # dimensions of temp plot
        rect_autocorr = [left, bottom_h, width, 0.25] # dimensions of x-histogram
        rect_autoconv = [left_h, bottom, 0.25, height] # dimensions of y-histogram

        # Make the three plots
        self.axTrace = self.fig.add_axes(rect_trace) # temperature plot
        self.ax_autocorr = self.fig.add_axes(rect_autocorr) # x histogram
        self.ax_autoconv = self.fig.add_axes(rect_autoconv) # y histogram

        # Remove the inner axes numbers of the histograms
        self.nullfmt = NullFormatter()
        self.ax_autocorr.xaxis.set_major_formatter(self.nullfmt)
        self.ax_autoconv.yaxis.set_major_formatter(self.nullfmt)

        self.axTrace.set_xlabel("Delay [fs]")
        self.axTrace.set_ylabel("Wavelength [nm]")
        self.ax_autoconv.set_title("Autoconvolution")
        self.ax_autocorr.set_title("Autocorrelation")
        
        #Load old data as reference
        '''file = r'Hardware\pyFROG\Old Examples\data\frg_trace_1580511001.pkl'
        data = pd.read_pickle(file)
        self.wave = data['wave'][0]
        trace = data['trace'][0]

        delay = np.linspace(-300,300,100)
        self.axTrace.pcolormesh(delay,self.wave,trace.T,cmap = "inferno")
        autocorr = np.sum(trace,axis = 1)
        autoconv = np.sum(trace,axis = 0)
        self.ax_autoconv.plot(autoconv,self.wave)
        self.ax_autocorr.plot(delay, autocorr)'''

        #peaks,_ = find_peaks(autocorr,distance=100)
        #results_half = peak_widths(autocorr,peaks,rel_height=0.5)[0]
        #autocorr_val = results_half[0]*(timeAxis[1]-timeAxis[0])
        #tempFWHM = autocorr_val/np.sqrt(2)
        self.axTrace.text(1.05, 1.49, f'Autocorrelation: {45.0:.1f} fs\nTemporal FWHM: {45/np.sqrt(2):.1f} fs', transform=self.axTrace.transAxes, fontsize=10,
                verticalalignment='top')

        super(frogTraceCanvas, self).__init__(self.fig)