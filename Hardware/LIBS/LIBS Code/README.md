# LIBS_GUI with 2-Axes Stage Control
Documentation: https://ying-wan.gitbook.io/libs-gui/

In this version of LIBS GUI, three hardwares are parallelly operated (Thorlabs ccs200, StellerNet UV spectrometer, and DG 645 delay generator). Additionally, a 2-axes Raspberry Pi controlled stage is opereated serially. Requirements for running the code:

•	Python 3.8 is needed.

•	After creating Python 3.8 environment in anaconda use: conda install anaconda

• Run uart_receiver.py on Raspberry Pi 

•	Python packages:

    o	conda install -c conda forge pyvisa
    o	pip install instrumental -lib
    o	pip install nicelib
    o	pip install -r requirement.txt 
    
## Note

•	Click “Disconnect all” before closing the GUI.

•	Click “Set ” after inputting any parameter.

• Wait a few minutes after booting the Raspberry Pi before running LIBSGUI.

• If the single shot button is disabled, return home.

# LIBS_GUI_190_500nm
In this version, Thorlabs spectrometer is removed and added 3 more high resolution (0.1 nm) StellarNet spectrometers

# LIBS_GUI_190_500nm-XPS
In this version, The stepper motor translation stage is replaced by XPS translation stage

# LIBS_GUI_190_500nm-XPS-Oci
In this version, a Tektronix ocilloscope is added to measure the laser energy for each laser shot

