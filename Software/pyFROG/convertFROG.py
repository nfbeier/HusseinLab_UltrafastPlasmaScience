# -*- coding: utf-8 -*-
"""
Created on Wed May 22 12:14:23 2024

@author: R2D2
"""

import pandas as pd
import h5py as h5
import matplotlib.pyplot as plt
import numpy as np
import glob
from scipy.interpolate import RectBivariateSpline
import os
from scipy.constants import c

plt.rc('font', size=16)          # controls default text sizes
plt.rc('axes', titlesize=20)     # fontsize of the axes title
plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=18)    # fontsize of the tick labels
plt.rc('ytick', labelsize=18)    # fontsize of the tick labels
plt.rc('legend', fontsize=16)    # legend fontsize
plt.rc('figure', titlesize=20)  # fontsize of the figure title
plt.rc("lines",lw = 2, markersize = 8)
plt.rcParams["axes.edgecolor"] = "black"
plt.rcParams["axes.linewidth"] = 1
plt.rcParams["axes.edgecolor"] = "0.3"
plt.rcParams["figure.facecolor"] = "w"

tnrfont = {'fontname':'Times New Roman'}

data_dir = r"C:\Users\R2D2\Documents\DATA\Spitfire Characterization\FROG Traces\20250408"
traces = sorted(glob.glob(f"{data_dir}/*shot1_comp_100*.h5"))
print(traces)

bkg = sorted(glob.glob(f"{data_dir}/*bkg*.h5"))[-1]
print(bkg)
bkg_data = h5.File(bkg)
bkg_trace = bkg_data["Trace"][:].T
#%%
shotNum = 0
data = h5.File(traces[shotNum],"r")
traceName = traces[shotNum].split("\\")[-1].split(".")[0]

delay = data["Delay"][:]
wave = data['Wavelength'][:]
trace = data["Trace"][:].T
trace_subbkg = trace - bkg_trace
trace_subbkg[trace_subbkg < 0.0025] = 0
new_wave = np.linspace(wave[0],wave[-1],len(wave), endpoint=True)

plt.pcolormesh(delay,wave,trace_subbkg,cmap = "inferno")
plt.colorbar()
#plt.ylim([350,450])
plt.xlabel("Delay [fs]")
plt.ylabel("Wavelength [nm]")
plt.title(traceName)
#%%
X ,Y = np.meshgrid(delay,wave)
X_new,Y_new = np.meshgrid(delay,new_wave)

interp = RectBivariateSpline(wave,delay,trace_subbkg)
interpTrace = interp(new_wave,delay)
fig, axs = plt.subplots(2,1,figsize = (6,10))

axs[0].pcolormesh(delay,wave,trace_subbkg,cmap = "inferno")
axs[0].set_ylim([350,450])
axs[0].set_xlabel("Delay [fs]")
axs[0].set_ylabel("Wavelength [nm]")
axs[0].set_title("Original Trace")

axs[1].pcolormesh(delay,new_wave,interpTrace,cmap="inferno")
axs[1].set_ylim([350,450])
axs[1].set_xlabel("Delay [fs]")
axs[1].set_ylabel("Wavelength [nm]")
axs[1].set_title("Interpolated Wavelength Trace")
plt.tight_layout()
#%%
delay_length = int(delay.shape[0])
wave_length = int(new_wave.shape[0])
delta_delay = delay[1]-delay[0]
delta_wave = new_wave[1]-new_wave[0]
center_wave = new_wave[int(wave_length/2)]
print(delay_length,wave_length,delta_delay,delta_wave,center_wave)
print(interpTrace.shape)
header = f'{delay_length}\t{wave_length}\t{delta_delay}\t{delta_wave}\t{center_wave}'
#%%
saveDir = f'{data_dir}/AnalyzedTraces/{traceName}'
if not os.path.exists(f'{data_dir}/AnalyzedTraces/{traceName}'):
    os.makedirs(saveDir)

#np.savetxt(f'{saveDir}/convertedFROG.frg', interpTrace, fmt="%f", header=header,comments='')
#%%
reconstructed_electric_time = glob.glob(f"{saveDir}/*256_100.bin.Ek*.dat")[0]
df_electricField_Time = pd.read_csv(reconstructed_electric_time, sep="\t", header=None)
int_time = df_electricField_Time[1]
phase_time = df_electricField_Time[2]
phase_time[int_time < 0.01*np.amax(int_time)] = 0

reconstructed_electric_freq = glob.glob(f"{saveDir}/*256_100.bin.Ew*.dat")[0]
df_electricField_Freq = pd.read_csv(reconstructed_electric_freq, sep="\t", header=None)
int_freq = df_electricField_Freq[1]
phase_freq = df_electricField_Freq[2]
phase_freq[int_freq < 0.01*np.amax(int_freq)] = 0
#%%
#exp_wave,exp_intensity = np.genfromtxt(r"C:\Users\R2D2\Documents\DATA\Spitfire Characterization\20240522\fullAmplify_FROGEntrance.csv",delimiter = ";",skip_header=48,usecols = (0,1),skip_footer=1,unpack = True)
#plt.plot(exp_wave[-1600:],exp_intensity[-1600:]/np.amax(exp_intensity[-1600:]))

reconstructed_electric_wave = glob.glob(f"{saveDir}/*256_100.bin.Speck*.dat")[0]
df_electricField_wave = pd.read_csv(reconstructed_electric_wave, sep="\t", header=None)
int_wave = df_electricField_wave[1]
plt.plot(df_electricField_wave[0],int_wave)

#%%
#exp_freq = c/exp_wave[-1600:]*1e-6
#exp_intensity_freq = c/exp_wave[-1600:]**2*exp_intensity[-1600:]
#exp_intensity_norm = exp_intensity_freq/np.amax(exp_intensity_freq)
plt.plot(exp_freq,exp_intensity_norm)
#%%
fig, axs = plt.subplots(1,2,figsize = (16,8))
phaseTimeAx = axs[0].twinx()
axs[0].plot(df_electricField_Time[0],int_time)
phaseTimeAx.plot(df_electricField_Time[0],phase_time,color= "r")
phaseTimeAx.set_ylim([-np.pi,np.pi])
axs[0].set_xlim([-200,200])

phaseFreqAx = axs[1].twinx()
axs[1].plot(df_electricField_Freq[0],int_freq,label = "FROG Reconstruction")
#axs[1].plot(exp_freq,exp_intensity_norm, label = "Measured Spectrum")
axs[1].legend(loc = 1,fontsize = 12)
axs[1].set_xlim([0.325,0.425])
phaseFreqAx.plot(df_electricField_Freq[0],phase_freq,color = "r")

phaseFreqAx.set_ylim([-np.pi,np.pi])
axs[0].set_xlabel("Time [fs]")
axs[0].set_ylabel("Intensity [a.u.]")
phaseTimeAx.set_ylabel("Phase [rad]",color = "red")
phaseTimeAx.tick_params(axis='y', colors='red')

axs[1].set_xlabel("Frequency [Phz]")
axs[1].set_ylabel("Intensity [a.u.]")
phaseFreqAx.set_ylabel("Phase [rad]")
phaseFreqAx.set_ylabel("Phase [rad]",color = "red")
phaseFreqAx.tick_params(axis='y', colors='red')

plt.tight_layout()
#%%(
phase_secdiv=np.gradient(np.gradient(np.gradient(phase_freq)))
plt.plot(df_electricField_Freq[0],phase_secdiv)
idx = np.argmax(int_freq)
print(idx)
print(phase_secdiv[idx],df_electricField_Freq[0][idx])