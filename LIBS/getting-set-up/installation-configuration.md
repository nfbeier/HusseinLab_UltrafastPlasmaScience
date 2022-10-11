# Installation/Configuration

## Installation

Repository: [https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience)

The code stored on GitHub is private. Message Nick for access if you don't already have access to it. Once accessible, you can download the files onto your local device by cloning it in terminal.

```bash
git clone https://github.com/nfbeier/HusseinLab_UltrafastPlasmaScience.git
```

## Included Files

<details>

<summary><a href="https://github.com/nfbeier/HusseinLab_UltrafastPlasmaScience/tree/main/LIBS">LIBS</a> : for control and user interfacing of the Thorlabs ccs200, StellerNet UV spectrometer, and DG 645 delay generator</summary>

[LIBS\_GUI.py](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS/LIBS\_GUI.py) **** : Main program that interfaces with hardware and calls upon LIBS\_GUI.ui to add functions to GUI widgets.

[LIBS\_GUI.ui](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS/LIBS\_GUI.ui) : User interfacing created through Designer which describes the design of the GUI.&#x20;

[lextab.py](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS/lextab.py)

[requirement.txt](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS/requirement.txt)

[stellarnet.hex](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS/stellarnet.hex)

[yacctab.py](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS/yacctab.py)

</details>

<details>

<summary><a href="https://github.com/nfbeier/HusseinLab_UltrafastPlasmaScience/tree/main/LIBS_withStage">LIBS_withStage</a> : for everything LIBS does plus control of and interfacing of a Raspberry Pi controlled 2 stepper motor stage</summary>

[LIBS\_GUI.py](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS\_withStage/LIBS\_GUI.py) : Main program that interfaces with hardware and calls upon LIBS\_GUI.ui to add functions to GUI widgets.

[LIBS\_GUI.ui](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS\_withStage/LIBS\_GUI.ui) : User interfacing created through Designer which describes the design of the GUI.&#x20;

[gui\_inputs.json](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS\_withStage/gui\_inputs.json) : Stored values of inputs given to the GUI from last use.

[manipulate\_json.py](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS\_withStage/manipulate\_json.py) : Reads from and writes to gui\_inputs.json to load GUI inputs from last use. Also automatically inputs last used values into GUI on opening.

[stage\_control.py](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS\_withStage/stage\_control.py) : Contains functions that interface with the Raspberry Pi (through UART serial communication) to control the stage.

[uart\_receiver.py](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS\_withStage/uart\_receiver.py) : Reads serially transmitted messages to control the stepper motors.\
_Note: This code must be installed on the Raspberry Pi and must be running when LIBS\_GUI.py is running. If using the lab's Pi, the code will run automatically on startup, if not using on lab Pi, see_ [configuring-your-raspberry-pi.md](configuring-your-raspberry-pi.md "mention")_._

</details>

[stellarnet\_driver3.pyd](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/stellarnet\_driver3.pyd) : Driver for the StellerNet UV spectrometer. \
_Note: Place in the folder you're using._

## Dependencies

LIBS GUI uses pyvisa, instrumental, nicelib, and requirement.&#x20;

```bash
conda install -c conda forge pyvisa
pip install instrumental -lib
pip install nicelib
pip install -r requirement.txt 
```

Note that [requirement.txt](https://github.com/nfbeier/HusseinLab\_UltrafastPlasmaScience/blob/main/LIBS/requirement.txt) is a local file meaning it must be downloaded from the repository and exist in the directory you are running the installation from.

&#x20;

**Additionally, Python must be of version 3.8.**\
****This can be done by creating a virtual environment in [Anaconda](https://www.anaconda.com) and then running:

```
conda install anaconda
```
