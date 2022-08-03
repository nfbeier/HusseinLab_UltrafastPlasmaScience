# LIBS_GUI with 2-Axes Stage Control
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
