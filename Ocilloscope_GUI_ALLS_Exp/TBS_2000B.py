import visa
import numpy as np
import matplotlib.pyplot as plt

# Connect to the oscilloscope
rm = visa.ResourceManager()
scope = rm.open_resource('USB0::0x0699::0x03C7::C020817::INSTR')

# Set up acquisition parameters
scope.write('DATa:SOUrce CH1')   # Select channel 4 as data source
scope.write('DATa:ENCdg RIBinary')   # Set binary data encoding
scope.write('WFMPre:XINcr?')   # Query the x-axis increment
xincr = float(scope.read())   # Convert the string response to a float
scope.write('WFMPre:YMUlt?')   # Query the y-axis scale
yscale = float(scope.read())   # Convert the string response to a float
scope.write('TRIGger:EDGE:SOURce CH1')   # Set the trigger source to channel 4
scope.write('TRIGger:EDGE:SLOPe POSitive')   # Set the trigger slope to positive
scope.write('TRIGger:LEVel CH4,0')   # Set the trigger level to 0V
scope.write('DAT:STAR 1')
scope.write('DAT:STOP 200000')
scope.write('CH1:SCALE 50')  # Set the vertical scale of channel 4 to 1V/div
scope.write('HOR:SCALE 0.040') # Set the horizontal scale to 1ms/div

# Arm the scope and wait for trigger
scope.write('ACQuire:STOPAfter SEQuence')   # Stop acquisition after one sequence
scope.write('ACQuire:STATE ON')   # Start acquisition
scope.query('*OPC?')   # Wait for acquisition to complete

# Read the acquired data
scope.write('CURVE?')   # Query the waveform data
data = scope.read_raw()   # Read the raw binary data
headerlen = 2 + int(data[1])   # Determine the length of the header
header = data[:headerlen]   # Extract the header
ADC_wave = data[headerlen:-1]   # Extract the ADC waveform data
ADC_wave = np.frombuffer(ADC_wave, 'B')   # Convert the binary data to integers
ADC_wave = ADC_wave - 127   # Convert the ADC values to signed integers
Volts_wave = yscale * ADC_wave   # Convert the ADC values to volts
Volts_wave = Volts_wave - np.mean(Volts_wave)
Time_wave = np.arange(0, xincr * len(Volts_wave), xincr)   # Generate the time axis

# Plot the waveform
plt.plot(Time_wave, Volts_wave)
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.show()
