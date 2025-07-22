import scipy as sp
import numpy as np

#Class SCRAM: used to import new SCRAM tables given a local file path. Data from the scram tables are stored in attributes of the class,
#and all attributes of the class can be accessed via SCRAM.attributes (e.g., Density (D), Electron temperature (Te), etc.)
# -the full matrix of j/k emissions are held in 224 (combos of ne, Te, tauR) x 1997 (photon energies) matrices accessed by SCRAM.j_table and
# SCRAM.k_table
# - a 4 dimensional matrix is constructed for compatibility with the RegularGridInterpolator function. The nested for-loops go though all
# combinations of ne, Te, and tauR, and assign a 1997x1 array of j/k to the corresponding index from SCRAM.j_table or SCRAM.k_table
# - SCRAM.j and SCRAM.k are used to access the interpolator objects that are passed to the Model() class. NOTE that logarithmic interp.
# is used, so one should exponentiate the values obtained in the Model.generateLayers() function
class SCRAM:
    
    def __init__(self, file_path):
        
        self.table = [line for line in open(file_path,"r")]
        self.meta_data = []
        for i in range(0,15): #metadata held in rows 0-15
            self.meta_data.append(self.table[i].strip().replace("\t"," "))
        
        #Initialize SCRAM with attributes from txt file (Not including j and k)
        self.attributes = []
        self.meta_data.append("UNITS:")
        dict_SCRAM = {}
        for row in self.table[15:46]: #18th to 46th row holds non-essential data, 15-17 holds density, temp, energy
          row = row.split("\t")
          dict_SCRAM[row[0]] =  np.asarray(row[1:]).astype(float)

        #Assigning each key in dictionary as an attribute of the class - this enables easy access for later use
        for key in dict_SCRAM:
          self.meta_data.append(key)
          attribute_name = key.split("(")[0].replace("/","_") #Attributes cannot have brackets or slashes, 
          self.attributes.append(attribute_name)              #refer to meta data for units (above line removes them)
          setattr(self,attribute_name,dict_SCRAM[key])

        #Extract absorbtion and emissivity
        self.j_table, self.en = [], [] #Only one energy axis specified because j and k have the same axis values
        for row in self.table[48:2045]:
          row = row.split("\t")
          self.en.append(row[0])
          self.j_table.append(row[1:])
        self.j_table, self.en = np.asarray(self.j_table).astype(float), np.asarray(self.en).astype(float)

        self.k_table = []
        for row in self.table[2047:]:
          row = row.split("\t")
          self.k_table.append(row[1:])
        self.k_table = np.asarray(self.k_table).astype(float)

        # Constructing a 4D array holding j/k values for each combination of T, ne, tauR 
        dens = np.unique(self.D) #4 density points --> view meta_data for ordering
        Te = np.unique(self.Te) #14 temp points --> view meta_data for ordering
        tauR = np.unique(self.tauR[self.tauR != 0]) # 3 tauR points excluding fluorescense --> [0.1, 1, 1000]
        self.j = np.zeros((len(dens), len(Te), len(tauR), len(self.en)))
        self.k = self.j #initialize blank matrices for j/k
        for ix,d in enumerate(dens): #loop through each combination and see which index it corresponds in the table of j/k values
            for jx,t in enumerate(Te): #j/k tables are 224x1997, # of ne points = 4, # Te points = 14, # of tauR points = 4
                for kx,tR in enumerate(tauR):                    # 4x14x4 = 224, 1997 photon energies used in for j/k emissions
                    for mx in range(len(self.D)):
                        if d == self.D[mx] and t == self.Te[mx] and tR == self.tauR[mx]:
                            self.j[ix][jx][kx] = self.j_table[:,mx]
                            self.k[ix][jx][kx] = self.k_table[:,mx]

        # #fluoresence kept in separate matrix from regular emissions
        self.j_fluor = np.zeros((len(dens), len(Te), len(self.en)))
        self.k_fluor = self.j_fluor #initialize blank matrices for j/k
        for ix,d in enumerate(dens):
          for jx,t  in enumerate(Te):
              for mx in range(len(self.D)):
                  if d == self.D[mx] and t == self.Te[mx]:
                      self.j_fluor[ix][jx] = self.j_table[:,mx]
                      self.k_fluor[ix][jx] = self.k_table[:,mx]

        #  Instantiate interpolation objects for j/k (log interpolation used)
        dens = np.log(dens); Te = np.log(Te); tauR = np.log(tauR); self.j = np.log(self.j) #logarithm of all quantities
        self.k = np.log(self.k);  self.j_fluor = np.log(self.j_fluor); self.k_fluor = np.log(self.k_fluor)

        self.j = sp.interpolate.RegularGridInterpolator((dens,Te,tauR),self.j) #interpolator objects
        self.k = sp.interpolate.RegularGridInterpolator((dens,Te,tauR),self.k)
        self.j_fluor = sp.interpolate.RegularGridInterpolator((dens,Te),self.j_fluor)
        self.k_fluor = sp.interpolate.RegularGridInterpolator((dens,Te),self.k_fluor)
