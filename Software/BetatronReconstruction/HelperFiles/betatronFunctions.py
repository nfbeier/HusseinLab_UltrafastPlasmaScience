# -*- coding: utf-8 -*-
"""
Created on Fri Feb  3 13:10:11 2023

@author: nfbei
"""

import scipy.constants as constant
from scipy.special import kv

def lorentzFactor(E_kin):
  #Input kinetic energy in MeV
  return E_kin/constant.value("electron mass energy equivalent in MeV") + 1

def E_crit(gamma,rho):
  #Returns synchrotron critical energy in units of keV
  return constant.hbar*3/2*gamma**3*constant.c/rho/constant.e/1000

def phi(E,E_crit,gamma,theta):
  return E/(2*E_crit)*(1+gamma**2*theta**2)**(3/2)

def betatronSource(en,eCrit):
  return (en/(eCrit))**2*kv(2/3,en/(eCrit))**2

def intensitySpectrum_Full(E,E_crit,gamma,theta):
  phi_val = phi(E,E_crit,gamma,theta)
  bessel = kv(2/3,phi_val)**2+gamma**2*theta**2/(1+gamma**2*theta**2)*kv(1/3,phi_val)**2
  return 3*constant.e**2/(16*constant.pi**3*constant.hbar*constant.c*constant.epsilon_0)*gamma**2*E**2/E_crit**2*bessel