# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 10:01:12 2023

@author: Nick
"""

import os, random
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.optimize import minimize

from torch import nn

from HelperFiles.betatronFunctions import betatronSource



class minimizationAlgorithm():
    
    def __init__(self,filterPack):
        self.filters = None
        self.ccdQE = self.load_CCDQE(r"D:\Research\UAlberta\Research\Code\Github\BetatronReconstruction\ALLS_FilterPackReconstruction\HelperFiles\Si_QE.txt")
        self.en = np.linspace(1,100,1000)
        self.dE = self.en[1]-self.en[0]
        
        #self.totalPathTransmission, self.filtersTransmission = 
        if filterPack == "StepWedgeFilters":
            self.transmissionPath, self.filters = self.load_transmissions(r"D:\Research\UAlberta\Research\Code\Github\BetatronReconstruction\ALLS_FilterPackReconstruction\HelperFiles\StepWedgeFilterPack\Filters.txt",\
                                r"D:\Research\UAlberta\Research\Code\Github\BetatronReconstruction\ALLS_FilterPackReconstruction\HelperFiles\StepWedgeFilterPack\TransmissionPath.txt")
        else:
            self.transmissionPath, self.filters = self.load_transmissions(r"D:\Research\UAlberta\Research\Code\Github\BetatronReconstruction\ALLS_FilterPackReconstruction\HelperFiles\RossPairFilterPack\Filters.txt",\
                                r"D:\Research\UAlberta\Research\Code\Github\BetatronReconstruction\ALLS_FilterPackReconstruction\HelperFiles\RossPairFilterPack\TransmissionPath.txt")
    def load_CCDQE(self,file_path):
        en_QE, QE = np.loadtxt(file_path,unpack = True,skiprows =1)
        return interp1d(en_QE,savgol_filter(QE,7,1)/100)
    
    def load_transmissions(self,filtersPath,tranmissionPath):
        filters = np.loadtxt(filtersPath,unpack = True)
        en,totalPathTransmission = np.loadtxt(tranmissionPath,unpack = True)

        return totalPathTransmission, filters[1:-1]
    
    def unfilteredBetatronCounts(self,eCrit):
        spectrum = betatronSource(self.en,eCrit)
        norm_spectrum = spectrum/np.amax(spectrum)
        spectrum_counts_unfiltered = norm_spectrum*self.en*self.dE*self.ccdQE(self.en)
        
        return spectrum_counts_unfiltered
    
    def filter_Fit(self, Ecrit,data_counts_norm):
      fit_spec = self.unfilteredBetatronCounts(Ecrit)
      betatron_counts = []
      for f in self.filters:
          betatron_counts.append(np.sum(fit_spec*f*self.transmissionPath))
      betatron_counts_norm = betatron_counts/np.average(betatron_counts)

      err = np.sum((betatron_counts_norm-data_counts_norm)**2)
      return err
  
    def calculateEcrit(self,data_counts_norm):
        fit = minimize(self.filter_Fit,x0 = np.array([random.uniform(10.0,25.0)]),args = (data_counts_norm),bounds = ((1,None),))
        fit_eCrit = round(fit.x[0],2)
        return fit_eCrit


device = "cpu"
print(f"Using {device} device")

# Define model
class NeuralNetworkTwoVariable_SWF(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(8, 64),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(64, 124),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(124, 64),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(64, 2)
        )

    def forward(self, x):
        # maxnorm weight before actual forward pass
        '''with torch.no_grad():
            norm = self.layer.weight.norm(2, dim=0, keepdim=True).clamp(min=self.weight_constraint / 2)
            desired = torch.clamp(norm, max=self.weight_constraint)
            self.layer.weight *= (desired / norm)'''
        
        logits = self.linear_relu_stack(x)
        return logits
    
    def deStandardizeData(self,y,mean,std):
        y = y*std+mean
        
        y_eCrit = np.exp(y[0])
        y_Amp = 10**(y[1])
        
        return y_eCrit, y_Amp

    
        #return sorted_y, 

# Define model
class NeuralNetworkOneVariable_SWF(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(8, 64),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(64, 124),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(124, 64),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        # maxnorm weight before actual forward pass
        '''with torch.no_grad():
            norm = self.layer.weight.norm(2, dim=0, keepdim=True).clamp(min=self.weight_constraint / 2)
            desired = torch.clamp(norm, max=self.weight_constraint)
            self.layer.weight *= (desired / norm)'''
        
        logits = self.linear_relu_stack(x)
        return logits

    def deStandardizeData(self,y,mean,std):
        y = y*std+mean
        
        y_eCrit = np.exp(y)
        
        return y_eCrit

# Define model
class NeuralNetworkTwoVariable_RPF(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(11, 64),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(64, 124),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(124, 64),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(64, 2)
        )

    def forward(self, x):
        # maxnorm weight before actual forward pass
        '''with torch.no_grad():
            norm = self.layer.weight.norm(2, dim=0, keepdim=True).clamp(min=self.weight_constraint / 2)
            desired = torch.clamp(norm, max=self.weight_constraint)
            self.layer.weight *= (desired / norm)'''
        
        logits = self.linear_relu_stack(x)
        return logits
    
    def deStandardizeData(self,y,mean,std):
        y = y*std+mean
        
        y_eCrit = np.exp(y[0])
        y_Amp = 10**(y[1])
        
        return y_eCrit, y_Amp
    
# Define model
class NeuralNetworkOneVariable_RPF(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear_relu_stack = nn.Sequential(
            nn.Linear(11, 64),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(64, 124),
            nn.ReLU(),
            #nn.Dropout(p=0.4),
            nn.Linear(124, 64),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        # maxnorm weight before actual forward pass
        '''with torch.no_grad():
            norm = self.layer.weight.norm(2, dim=0, keepdim=True).clamp(min=self.weight_constraint / 2)
            desired = torch.clamp(norm, max=self.weight_constraint)
            self.layer.weight *= (desired / norm)'''
        
        logits = self.linear_relu_stack(x)
        return logits

    def deStandardizeData(self,y,mean,std):
        y = y*std+mean
        
        y_eCrit = np.exp(y)
        
        return y_eCrit
    
if __name__ == "__main__":
    os.chdir(r"D:\Research\UAlberta\Research\Data\Neural Network Training\September 2023\Step Wedge Filters\StepWedgeFilters_Dataset1\TrainingSet")
    
    minAlg = minimizationAlgorithm("StepWedgeFilters")

    print(minAlg.calculateEcrit([1.94302338, 1.87056397, 1.78726194, 0.90780708, 0.57076103, 0.39520886,
     0.29573674, 0.229637  ]))