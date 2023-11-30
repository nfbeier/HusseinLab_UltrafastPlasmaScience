# -*- coding: utf-8 -*-
"""
Created on Fri Feb  3 12:51:07 2023

@author: nfbei
"""

from physdata.xray import fetch_coefficients
import numpy as np
from scipy.interpolate import interp1d
import pandas as pd

class FilterArray():
  def __init__(self,en,filters):
      
    self.elemTable = pd.read_hdf(r"C:\Users\nfbei\Documents\Research\Code\X-Ray Materials\ElementTables\PhysPropTable",key = "df")
    self.transmission_array = []
    
    for (mat,thick) in filters:
        transmission = self.filter_transmission(en,mat,thick)
        self.transmission_array.append(transmission)

  def getRossPairs(self,filterPairs):
    transmission_RossPair = []
    for (mat1,mat2) in filterPairs:
        transmission = self.transmission_array[mat1]- self.transmission_array[mat2]
        transmission = np.where(transmission<0, 0, transmission)
        transmission_RossPair.append(transmission)

    return transmission_RossPair

  def getFilterTransmission(self,filter_numbers = None):
    if filter_numbers is None:
      return self.transmission_array
    return self.transmission_array[filter_numbers]

  def getMaterialValues(self,material):
    if isinstance(material,int):
        Z = material
        PP = self.elemTable.iloc[Z-1]
    elif isinstance(material,str):
        PP = self.elemTable.loc[(self.elemTable["Symbol"] == material) | (self.elemTable["Name"] == material)]
        Z = PP.index[0] + 1
        PP = PP.iloc[0]
    return PP, Z

  def PhotonAttenuation(self,Z,energy_MeV):
    data = np.array(fetch_coefficients(int(Z)))

    enData = data[:,[0]].T
    muData = data[:,[1]].T

    mu_interp = interp1d(np.log(enData[0]),np.log(muData[0]))
    mu = np.exp(mu_interp(np.log(energy_MeV)))
    return mu

  def filter_transmission(self,energy_keV, material, thickness_um):
    PP, Z = self.getMaterialValues(material)
    density = float(PP["Density"])
    energy_MeV = energy_keV/1000 #photon energy in MeV
    thickness_cm = thickness_um*1e-4  #material thickness in cm

    Mu = self.PhotonAttenuation(Z, energy_MeV)
    T = np.exp(-1*Mu*thickness_cm*density) #fractional transmission of photons at each energy;
    return T
  
  def updateFilters(self,en,filters):
      for (mat,thick) in filters:
        transmission = self.filter_transmission(en,mat,thick)
        self.transmission_array.append(transmission)
        
if __name__ == "__main__":
    filters = (("Zn",350),("Mo",100),("Ag",75),("Sn",100),("Sn",150),("Nd",100),("Nd",200),("Ta",50),("Ta",127),("Pb",125))
    en = np.linspace(1,100,1000)
    transmission_NoFilter = [en*[1]] # Begin with unfiltered transmission for Images
    
    filterPairs = ((1,0),(2,1),(3,2),(5,4),(7,6),(9,8))
    RossPairs = FilterArray(en,filters)