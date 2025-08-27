import pathlib
import sys

cur_dir = pathlib.Path(__file__)
sys.path.append(str(cur_dir.parent.parent))

from specdriver.spectrometer import GetDLLversion, SpectrometersAvailable, SPECTROMETER, \
                                 DISB, DetectorType, Firmware, AUX_OUTPUT_MODE, TEMPERATURE_FORMAT, \
                                 GAIN_MODE, WavelengthCalibration, LinearityCalibration, Information, \
                                 GPIO_input, GPIO_output, HW_AVERAGING_STATUS, Trigger_mode

# Initialize the spectrometer(s) using their device manager index
#
# Note that you are also able to initialize the spectrometer using the serial number. For example, Spectrometer("123456")
spectrometer = SPECTROMETER(0)

# Print the hardware information available for the currently connected spectrometer
print(spectrometer.m_info)

# Set the desired exposure time for the upcoming measurement
spectrometer.SetExposureTime(10.0) # 10.0 ms
print(f'\nThe spectrometer exposure time has been set to {spectrometer.GetExposureTime()} ms')

# Change the region of interest for the measurement such that it only includes the part of the spectrum which you are interested in

# You may need to change the wavelength boundaries, depending on which spectrometer you have connected.
spectrometer.SetRegionOfInterest(190.0,435.0) # 400.0 nm to 800.0 nm
wl_start, wl_end, pix_start, pix_end = spectrometer.GetRegionOfInterest()
print(f"\nThe spectrometer region of interest has been set from {wl_start:.2f} nm to {wl_end:.2f} nm, corresponding to a pixel range of {pix_start} to {pix_end}")

# Make sure that all possible methods of triggering the spectrometer are enabled before starting a measurement
#
# SPI trigger : Enabled
# External HW trigger : Enabled
# Interal trigger : Enabled
spectrometer.SetTriggerMode(Trigger_mode(SPI_trigger_enabled=True, ExternalHW_trigger_enabled=True, Internal_trigger_enabled=True))

trig_mode = spectrometer.GetTriggerMode()
if trig_mode.SPI_trigger_enabled and trig_mode.ExternalHW_trigger_enabled and trig_mode.Internal_trigger_enabled:
    print("\nAll trigger modes have been enabled")

# Get a single spectrum measurement from the spectrometer
print('\nRead out the 16-bit ADC count values for the first 10 pixels of the returned spectrum:')
print(len(spectrometer.GetSingleSpectrum()))
print('\nWavelength in nm for the first 10 pixels of the returned spectrum:')
print(spectrometer.GetWavelengthAxis()[:10])

# Acquire multiple spectra in one measurement, achieving the highest framerate possible for the current settings.
#
# A vector containing the elapsed time for each spectral measurement since the start of the first measurement in the series is also
# returned and can be used to create DateTime stamps for each measurement in the series
multiple_spectra, time_elapsed_us = spectrometer.GetMultipleSpectra(10)

# An easy way of figuring out what the highest possible framerate is, using the current settings,
# is by calling the GetFramerate method of the spectrometer class
framerate = spectrometer.GetFramerate()
print(f'\nCurrent framerate: {framerate} [Hz]')
