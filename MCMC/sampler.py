from simulator import SCRAMTarget
import numpy as np


def log_likelihood(theta, y, yerr, emiss_generator):
    
    #Separate front/back experimental data
    spec_VH, spec_HR = y
    err_VH, err_HR = yerr
    
    #Produce SCRAM emission lines using SCRAMTarget object from argument
    emiss_generator.temps = theta
    model_VH,model_HR = emiss_generator.model()


    log_likelihood_VH = -1/2 * np.sum((spec_VH - model_VH) ** 2/err_VH**2) #front side spectra
    log_likelihood_HR = -1/2 * np.sum((spec_HR - model_HR) ** 2/err_HR**2) #rear side spectra

    return log_likelihood_VH+log_likelihood_HR

def log_prior(theta):
    temp = theta
    if 0 < temp < 4:
        return 0.0
    return -np.inf


def log_probability(theta, y, yerr, emiss_generator):
    lp = log_prior(theta)
    if not np.isfinite(lp):
        return -np.inf
    return lp + log_likelihood(theta, y, yerr, emiss_generator)