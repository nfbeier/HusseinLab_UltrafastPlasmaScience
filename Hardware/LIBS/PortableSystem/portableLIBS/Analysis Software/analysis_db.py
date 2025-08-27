import os, sys
import h5py
import numpy as np
import time
from scipy import sparse
from scipy.sparse.linalg import spsolve
import matplotlib.pyplot as plt
import scienceplots
import pandas as pd
plt.style.use(["science", "notebook", 'retro'])
plt.rcParams["font.family"] = "Times New Roman"


energy = {"120": "4.8 $\pm$ 0.4",
          "130": "8.2 $\pm$ 0.5",
          "140": "11.8 $\pm$ 0.6",
          "150": "15.1 $\pm$ 0.8",
          "160": "18.2 $\pm$ 0.8",
          "170": "21.2 $\pm$ 0.8",
          "179": "23.5 $\pm$ 0.8",}
energy_float = {
            "120": (4.8, 0.4),
            "130": (8.2, 0.5),
            "140": (11.8, 0.6),
            "150": (15.1, 0.8),
            "160": (18.2, 0.8),
            "170": (21.2, 0.8),
            "179": (23.5, 0.8)
        }

pulse_duration = "7 $\pm$ 1 ns"       # ns
spot_size = "50 x 60 $\pm$ 2 μm"      # micron
intensity_dict = {}

def intensity(energy, pulse_duration=7e-9):
    spot_size_cm = np.pi * (50e-6 * 60e-6) * 10000 / (4)
    intensity_cm = 2 * energy[0] / (100*spot_size_cm * pulse_duration)
    intensity_error_cm = intensity_cm* ( (energy[1] / energy[0]) + (2/25) + (2/30) + (1/7)) 
    return intensity_cm, intensity_error_cm


for i in energy_float.keys():
    intensity_cm, intensity_error_cm = intensity(energy_float[i])
    
    intensity_dict = {}

    for i in energy_float.keys():
        intensity_cm, intensity_error_cm = intensity(energy_float[i])
        intensity_dict[i] = {"intensity": intensity_cm, "uncertainty": intensity_error_cm}


def h5_directory_to_single_h5_file(directory, background_subfolder="background",
                                    output_file=None, intensity_key='Intensity', output_dir="analysis", verbose=False):
    """
    Merges multiple HDF5 files in a directory into a single HDF5 file.

    Args:
        directory (str): The directory containing the HDF5 files to be merged.
        background_subfolder (str, optional): The subfolder within the directory that contains the background HDF5 files. Defaults to "background".
        output_file (str, optional): The name of the output HDF5 file. If not provided, a default name will be generated based on the current timestamp. Defaults to None.
        intensity_key (str, optional): The key of the dataset within each HDF5 file that contains the intensity data. Defaults to 'Intensity'.
        verbose (bool, optional): If True, additional information will be printed during the merging process. Defaults to False.

    Raises:
        AssertionError: If the directory or background subfolder does not exist, or if there are no HDF5 files in the directory or background subfolder.

    Returns:
        None
    """
    # Start the timer to measure the duration of the merging process
    st = time.time()

    # Get all the h5 files in the directory
    if verbose:
        print("Merging h5 files in directory:", directory)
        print("Background subfolder:", os.path.join(directory, background_subfolder))

    # Ensure the specified directory exists
    assert os.path.exists(directory), "Directory does not exist"
    # Ensure the background subfolder exists within the specified directory
    assert os.path.exists(os.path.join(directory, background_subfolder)), "Background subfolder does not exist"

    if os.path.exists(os.path.join(directory, output_dir)) == False:
        os.makedirs(os.path.join(directory, output_dir))

    # List all .h5 files in the directory excluding the output file
    files = [f for f in os.listdir(directory) if f.endswith('.h5') and f != output_file]
    # List all .h5 files in the background subfolder
    background_files = [f for f in os.listdir(os.path.join(directory, background_subfolder)) if f.endswith('.h5')]

    # Ensure there are .h5 files in the directory
    assert len(files) > 0, "No h5 files in directory"
    # Ensure there are .h5 files in the background subfolder
    assert len(background_files) > 0, "No h5 files in background subfolder"

    # If no output file is specified, create a default one with a timestamp
    if output_file is None:
        output_file = "h5_directory_to_single_h5_file_" + time.strftime("%Y%m%d-%H%M%S") + ".h5"
        output_file = os.path.join(directory, output_dir, output_file)
    else:
        # Ensure the output file has the .h5 extension
        if not output_file.endswith('.h5'):
            output_file = output_file + ".h5"
        output_file = os.path.join(directory, output_dir, output_file)


    # Create or open the output .h5 file for writing
    with h5py.File(os.path.join(directory, output_file), 'w') as f:

        # Open the first h5 file in the directory
        with h5py.File(os.path.join(directory, files[0]), 'r') as f2:
            # Get the wavelength dataset from the first h5 file
            f.create_dataset("Wavelength", data=f2['Wavelength'][:])

        # Create a group for intensities in the output file
        intensities = f.create_group(intensity_key)

        # Loop through each .h5 file and copy its intensity data to the output file
        for file in files:
            with h5py.File(os.path.join(directory, file), 'r') as f2:
                f3 = intensities.create_dataset(file, data=f2[intensity_key][:])
                # Copy metadata from the source file to the destination file
                for key, value in f2.attrs.items():
                    f3.attrs[key] = value
        # Create a group for background data in the output file
        backgrounds = f.create_group("Background")
        # Loop through each .h5 file in the background subfolder and copy its data to the output file
        for file in background_files:
            with h5py.File(os.path.join(directory, background_subfolder, file), 'r') as f2:
                backgrounds.create_dataset(file, data=f2[intensity_key][:])
        # Copy attributes from the first intensity dataset to the root .h5 attributes
        first_intensity_dataset = list(intensities.keys())[0]
        for key, value in intensities[first_intensity_dataset].attrs.items():
            f.attrs[key] = value

    # If verbose mode is enabled, print the details of the merging process
    if verbose:
        print(f"Shot files merged: {len(files)}")
        print(f"Background files merged: {len(background_files)}")
        print("Files merged in", time.time() - st, "seconds")
        print("Output file:", os.path.join(directory, output_file))
    return os.path.join(directory, output_file)

def consolidated_h5_file_analysis(ch5file, output_file=None, intensity_key='Intensity', background_key="Background", output_dir="analysis", verbose=False):
    """
    Perform analysis on a consolidated HDF5 file.

    Args:
        ch5file (str): The path to the consolidated HDF5 file.

    Returns:
        None
    """
    st = time.time()
    # If no output file is specified, create a default one with a timestamp
    if output_file is None:
        output_file = "bkg_sub_mean_snr_file_analysis_" + time.strftime("%Y%m%d-%H%M%S") + ".h5"
        output_file = os.path.join(os.path.dirname(ch5file), output_file)
    else:
        # Ensure the output file has the .h5 extension
        if not output_file.endswith('.h5'):
            output_file = output_file + ".h5"
        output_file = os.path.join(os.path.dirname(ch5file), output_file)

    # Open the consolidated HDF5 file in read mode
    with h5py.File(ch5file, 'r') as f:
        backgrounds = []
        for file in f[background_key]:
            backgrounds.append(f[background_key][file][:])
        backgrounds = np.array(backgrounds)
        if verbose:
            print("Backgrounds shape:", backgrounds.shape)


        intensities = []
        for intensity in f[intensity_key]:
            tmp = intensities.append(f[intensity_key][intensity][:])
        intensities = np.array(intensities)

        if verbose:
            print("Intensities shape:", intensities.shape)

    # Perform analysis on the intensity and background data
    bkg_mean = np.mean(backgrounds, axis=0)
    bkg_std = np.std(backgrounds, axis=0)
    signal_mean = np.mean(intensities, axis=0)
    signal_mean_bkg_sub = signal_mean - bkg_mean
    signal_mean_std = np.std(intensities, axis=0)

    snr = signal_mean_bkg_sub / bkg_std
    
    # Create or open the output .h5 file for writing
    with h5py.File(output_file, 'w') as f:
        # Add metadata for date and time created
        f.attrs['DateCreated'] = time.strftime("%Y-%m-%d")
        f.attrs['TimeCreated'] = time.strftime("%H:%M:%S")
        # Create a group for the analysis results in the output file
        analysis = f.create_group("Analysis")
        # Create datasets for the calculated values
        analysis.create_dataset("BackgroundMean", data=bkg_mean)
        analysis.create_dataset("BackgroundStd", data=bkg_std)
        analysis.create_dataset("SignalMean", data=signal_mean)
        analysis.create_dataset("SignalMeanBackgroundSubtracted", data=signal_mean_bkg_sub)
        analysis.create_dataset("SNR", data=snr)
        analysis.create_dataset("SignalMeanStd", data=signal_mean_std)

        bkg_sub = f.create_group("BackgroundSubtracted")
        with h5py.File(ch5file, 'r') as f2:
            f.create_dataset("Wavelength", data=f2['Wavelength'][:])
            # copy the metadata over
            for key, value in f2.attrs.items():
                    f.attrs[key] = value

            for intensity in f2[intensity_key]:
                f3 = bkg_sub.create_dataset(intensity, data=f2[intensity_key][intensity][:] - bkg_mean)
                # Copy metadata from the source file to the destination file


    if verbose:
        print("Analysis completed in", time.time() - st, "seconds")
        print("Output file:", output_file)
    return output_file

def continuum_normalization_minmax_h5(ah5file, output_file=None, intensity_key='Intensity', background_key="Background", output_dir="analysis", verbose=False):
    """
    Perform continuum normalization on an analyzed consolidated HDF5 file using min-max normalization.

    Args:
        ah5file (str): The path to the analyzed consolidated HDF5 file.
        output_file (str, optional): The name of the output HDF5 file. If not provided, a default name will be generated based on the current timestamp. Defaults to None.
        intensity_key (str, optional): The key of the dataset within the analyzed consolidated HDF5 file that contains the intensity data. Defaults to 'Intensity'.
        background_key (str, optional): The key of the dataset within the analyzed consolidated HDF5 file that contains the background data. Defaults to 'Background'.
        verbose (bool, optional): If True, additional information will be printed during the continuum normalization process. Defaults to False.

    Returns:
        str: The path to the output HDF5 file.
    """
    st = time.time()
    # If no output file is specified, create a default one with a timestamp
    if output_file is None:
        output_file = "continuum_normalization_minmax_h5_" + time.strftime("%Y%m%d-%H%M%S") + ".h5"
        output_file = os.path.join(os.path.dirname(ah5file), output_file)
    else:
        # Ensure the output file has the .h5 extension
        if not output_file.endswith('.h5'):
            output_file = output_file + ".h5"
        output_file = os.path.join(os.path.dirname(ah5file), output_file)


    # Open the consolidated HDF5 file in read mode
    with h5py.File(ah5file, 'r') as f:
        int_time = float(f.attrs["Integration Time"])
        wavelength = f["Wavelength"][:]
        bkg_sub = []
        for file in f["BackgroundSubtracted"]:
            bkg_sub.append(f["BackgroundSubtracted"][file][:])
        std_intensities = f["Analysis"]["SignalMeanStd"][:]
        bkg_sub = np.array(bkg_sub)
        if verbose:
            print("Background Subtracted shape:", bkg_sub.shape)

    bkg_sub_mean = np.mean(np.array(bkg_sub), axis=0)
    continuum, spectra = Baseline_correction(bkg_sub_mean, 10**5, 0.01)
    continuum_std_int = std_intensities / continuum

    # Load the correction factor data from the CSV file
    correction_data = pd.read_csv('Ibsen_correction_factor.csv')

    # Extract the wavelength and correction factor columns
    wavelength_correction = correction_data['Wavelength'].values
    correction_factor = correction_data['Correction Factor'].values

    # Interpolate the correction factor to match the wavelength of the spectrum
    correction_factor_interp = np.interp(wavelength, wavelength_correction, correction_factor)

    # Apply the correction factor to the continuum normalized intensity
    Irradiance_corrected_intensity = spectra * correction_factor_interp * (250/int_time) # 250 ms used for calibration curve.



    cont_norm_individual = []
    for i in bkg_sub:
        tmp = np.array(i / continuum)
        tmp[tmp < 0] = 0
        cont_norm_individual.append(tmp)

    # Create or open the output .h5 file for writing
    with h5py.File(output_file, 'w') as f:
        # Add metadata for date and time created
        f.attrs['DateCreated'] = time.strftime("%Y-%m-%d")
        f.attrs['TimeCreated'] = time.strftime("%H:%M:%S")
        f.create_dataset("Continuum", data=continuum)
        f.create_dataset("ContinuumNormalizedStd", data=continuum_std_int)
        f.create_dataset("Intensity", data=spectra)
        f.create_dataset("minmax_Intensity", data=minmax_normalize(spectra))
        f.create_dataset("IrradianceCorrectedIntensity", data=Irradiance_corrected_intensity)
        cont_norm = f.create_group("ContinuumNormalized")
        with h5py.File(ah5file, 'r') as f2:
            f.create_dataset("Wavelength", data=f2['Wavelength'][:])
            f.create_dataset("SNR", data=f2["Analysis"]["SNR"][:])
            # copy the metadata over
            for key, value in f2.attrs.items():
                    f.attrs[key] = value

            for intensity in f2["BackgroundSubtracted"]:
                cont_norm.create_dataset(intensity, data=cont_norm_individual.pop(0))

    if verbose:
        print("Continuum normalization completed in", time.time() - st, "seconds")
        print("Output file:", output_file)

    return output_file

def plot_analyzed_data(analyzed_h5_file, do_save=False, plot=True, dpi=300, figsize=(16, 9), font_size=12, figdir=None, verbose=False):
    with h5py.File(analyzed_h5_file, 'r') as f:
        continuum = f["Continuum"][:]
        wavelength = f["Wavelength"][:]
        snr = f["SNR"][:]
        cont_norm_std = f["ContinuumNormalizedStd"][:]
        cont_norm_intensity = f['Intensity'][:]
        minmax_intensity = f["minmax_Intensity"][:]
        qsdelay = f.attrs["Q Switch Delay"]
        sample_id = f.attrs["Sample ID"]
        bstnum = f.attrs["Shot Burst Number"]
        IrradianceCorrectedIntensity = f["IrradianceCorrectedIntensity"][:]

    if sample_id == "":
        print("No sample ID found!")   
    
    if not figdir:
        if os.path.exists(os.path.join(os.path.dirname(analyzed_h5_file), "figs")) == False:
            os.makedirs(os.path.join(os.path.dirname(analyzed_h5_file), "figs"))
        figdir = os.path.join(os.path.dirname(analyzed_h5_file), "figs")

    plot_spectra_rectangular(wavelength, continuum, qsdelay=qsdelay, sample_id=sample_id, title="Continuum", plot=plot, dpi=dpi, figsize=figsize, font_size=font_size, figdir=figdir, do_save=do_save, bstnum=bstnum, verbose=verbose)
    plot_spectra_rectangular(wavelength, cont_norm_intensity, std=cont_norm_std, sample_id=sample_id, qsdelay=qsdelay, title="Continuum Normalized Intensity with std dev", plot=plot, dpi=dpi, figsize=figsize, font_size=font_size, figdir=figdir, bstnum=bstnum, do_save=do_save, verbose=verbose)
    plot_spectra_rectangular(wavelength, cont_norm_intensity, qsdelay=qsdelay, sample_id=sample_id, title="Continuum Normalized Intensity", plot=plot, dpi=dpi, figsize=figsize, font_size=font_size, figdir=figdir, do_save=do_save, bstnum=bstnum, verbose=verbose)
    plot_spectra_rectangular(wavelength, minmax_intensity, qsdelay=qsdelay, sample_id=sample_id, title="MinMax Normalized Intensity", plot=plot, dpi=dpi, figsize=figsize, font_size=font_size, figdir=figdir, do_save=do_save, bstnum=bstnum, verbose=verbose)
    plot_spectra_rectangular(wavelength, snr, qsdelay=qsdelay, sample_id=sample_id, title="Signal to Noise Ratio", ylabel='SNR', plot=plot, dpi=dpi, figsize=figsize, font_size=font_size, figdir=figdir, do_save=do_save, bstnum=bstnum, verbose=verbose)
    plot_spectra_rectangular(wavelength, 10*np.log10(snr), qsdelay=qsdelay, sample_id=sample_id, title="Signal to Noise Ratio, dB", ylabel='SNR [dB]', plot=plot, dpi=dpi, figsize=figsize, font_size=font_size, figdir=figdir, do_save=do_save, bstnum=bstnum, verbose=verbose)
    plot_spectra_rectangular(wavelength, IrradianceCorrectedIntensity, qsdelay=qsdelay, sample_id=sample_id, title="Irradiance Corrected Intensity", ylabel="Irradiance [uW/cm^2/nm]", plot=plot, dpi=dpi, figsize=figsize, font_size=font_size, figdir=figdir, do_save=do_save, bstnum=bstnum, verbose=verbose)

def plot_spectra_rectangular(x=None, y=None, qsdelay=None, do_save=False, plot=True, dpi=300, figsize=(16, 9), font_size=12, sample_id="", title="", ylabel="Counts [arb]", std=None, figdir="", bstnum=1, verbose=False):
    st = time.time()
    if y is None:
        print("No intensity data provided!")
        return
    plt.rcParams.update({'font.size': font_size})
    plt.rcParams['figure.dpi'] = dpi
    plt.gcf().set_size_inches(figsize[0], figsize[1])

    if x is None or len(x) == 0:
        plt.plot(y, label=f"{sample_id} Intensitity", linewidth=0.7)
        plt.xlabel("Pixel Number")
    else:
        plt.plot(x, y, label=f"{sample_id} Intensitity", linewidth=0.7)
        plt.xlabel("Wavelength (nm)")
    plt.ylabel(ylabel)

    if std is not None:
        if verbose:
            print(std.shape, y.shape)
        if std.shape == y.shape:
            if verbose:
                print("Plotting standard deviation")
                plt.fill_between(x, y-std, y+std, alpha=0.3, label="Standard Deviation")
        else:
            print("Standard deviation shape does not match the intensity shape!")

    if title and sample_id:
        plottitle = f"{title}_{sample_id}"
    elif title:
        plottitle = title
    elif sample_id:
        plottitle = f"{sample_id}_Spectra"
    plt.title(plottitle)

    if qsdelay:
        try:
            plt.text(0.02, 0.95, f"Wavelength: 532 nm\nEnergy: {energy[qsdelay]} mJ\nPulse Duration: {pulse_duration}\nSpot Size: {spot_size}\nIntensity: {intensity_dict[qsdelay]['intensity']:1.1e} $\pm$ {intensity_dict[qsdelay]['uncertainty']:1.0e} W/cm^2\nBurst Number: {bstnum}",
                horizontalalignment='left', verticalalignment='top', transform=plt.gca().transAxes)
        except Exception as e:
            print("Failed to set text on plot\n", e)

    plt.legend(loc='upper right', fontsize='small')

    if do_save:
        plt.savefig(os.path.join(figdir, plottitle + ".png"))
    if plot:
        plt.show()


    if verbose:
        print("Plotting took", time.time() - st, "seconds")


## Helper functions below ##
def minmax_normalize(intensities):
    min_int = np.min(intensities)
    max_int = np.max(intensities)
    return (intensities - min_int) / (max_int - min_int)

def baseline_als(intensity, lambda_param, asymmetry_param, num_iterations=10):
    # Determine the length of the input intensity array
    data_length = len(intensity)
    
    # Create a second-order difference matrix
    difference_matrix = sparse.csc_matrix(np.diff(np.eye(data_length), 2))
    
    # Initialize weights to be ones
    weights = np.ones(data_length)
    
    # Perform iterations to estimate the baseline
    for _ in range(num_iterations):
        # Create a diagonal matrix using the weights
        diagonal_weights = sparse.spdiags(weights, 0, data_length, data_length)
        
        # Construct the matrix Z for the least squares problem
        matrix_z = diagonal_weights + lambda_param * difference_matrix.dot(difference_matrix.transpose())
        
        # Solve the least squares problem to estimate the baseline
        estimated_baseline = spsolve(matrix_z, weights * intensity)
        
        # Update the weights based on asymmetry to refine the estimation
        weights = asymmetry_param * (intensity > estimated_baseline) + (1 - asymmetry_param) * (intensity < estimated_baseline)
    
    # Return the estimated baseline
    return estimated_baseline

def Baseline_correction(intensity, lam, p):
    # Estimate baseline using baseline_als for the given intensity spectrum
    baseline = baseline_als(intensity, lam, p)
    
    # Perform continuum normalization by dividing original intensity by the baseline
    intensity_crr = (intensity-baseline) / baseline
        
    # Return the calculated baseline and baseline-corrected intensity
    return baseline, intensity_crr