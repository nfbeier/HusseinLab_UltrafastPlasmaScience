from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, MaxNLocator

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
        
        super(frogTraceCanvas, self).__init__(self.fig)