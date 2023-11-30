import pandas as pd
import tables
import scipy as sp
import numpy as np
import glob 
import os

#Function that obtains interpolator for k and j values, and an array energy axis. Only argument is SCRAM table directory
def get_SCRAM(SCRAM_path):	

    #import SCRAM files as a dataframe
    SCRAMfiles = sorted(glob.glob(SCRAM_path))
    k = pd.read_hdf(SCRAMfiles[0])
    j = pd.read_hdf(SCRAMfiles[1])
    conditions = pd.read_hdf(SCRAMfiles[2])

    #Gather SCRAM temps, energy axis, and absorbtion/emissvity as arrays
    temps = conditions["Te(eV)"].to_numpy().astype(float)
    k = k.to_numpy().astype(float)
    k_enrg_axs = k[:,0] #first column of SCRAM has energy axis
    k = k[:,1:] #remaning columns hold absorbtions
    j = j.to_numpy().astype(float)
    j = j[:,1:] #disregard first column of emissivity table (energy axis)

    #2D interpolation (T and E) to find unknown j and k values
    # values = (np.log(k_enrg_axs),np.log(temps[1:])) #tuple of the form ([])
    k = sp.interpolate.interp2d(k_enrg_axs, temps, k.flatten(),kind='linear')
    j = sp.interpolate.interp2d(k_enrg_axs, temps, j.flatten(), kind='linear')

    return k, j, k_enrg_axs


#Function to import experimental spectra and returns interpolators for VH and HR spectra and error
def get_expdata(expr_data_path, shot_nums):

    #Change to directory of data and import all files (Pick folder for a single date e.g. all Dec 14 shots)
    os.chdir(expr_data_path)
    shot_list = sorted(glob.glob("*"))


    #Extract spectra from shot_nums with "best focus" and laser conditions 
    spec_VH,spec_HR = [],[]
    shot = []
    for i in shot_nums:
        shot = pd.read_hdf(shot_list[i])
        spec_VH.append(shot["Spectrum_VonHamos"]*1000)
        spec_HR.append(shot["Spectrum_Kalpha"]*1000/2)
        # spec_Kbeta = shot["Spectrum_Kbeta"]*1000/2

    #Obtain energy axes, error in intensity, and average intensity
    enrg_ax_VH, enrg_ax_HR = shot["enAxis_VonHamos"], shot["enAxis_Kalpha"]
    VH_err, HR_err = np.std(spec_VH, axis=0), np.std(spec_HR, axis=0)
    spec_VH, spec_HR = np.average(spec_VH, axis = 0), np.average(spec_HR, axis = 0)

    #interpolate spectra and errors
    spec_VH, spec_HR = sp.interpolate.interp1d(enrg_ax_VH,spec_VH), sp.interpolate.interp1d(enrg_ax_HR,spec_HR)
    VH_err, HR_err = sp.interpolate.interp1d(enrg_ax_VH, VH_err), sp.interpolate.interp1d(enrg_ax_HR, HR_err)

    return spec_VH, spec_HR, VH_err, HR_err
