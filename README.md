---
Repository Description: 'Last Edited: July 29, 2025'
---

[![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)

# Overview

Github repository for hardware and software interfacing of the smart system used by the Hussein Ultrafast Plasma Science group at the University of Alberta for experiments LIBS and high-repetition-rate, femtosecond laser experiments.

The smart system aims to interface a collection of hardware components necessary to perform high intensity laser-plasma interactions including FLIR Blackfly CCD, Newport XPS-D8 Motion Controller,
Agilent XGS-600 Vacuum Controller, Andor iKon-M Vacuum X-ray CCD, and more. The various equipment will be controlled using Python code, and be designed in a modular structure to allow for quick
changes in experimental setups.

# Python Version
We are standardized on Python 3.10 for all software in this repo. However, usage of the LIBS code with Stellarnet spectrometers requires Python 3.8

# Importing Driver Code
This project aims to provide a consistent and reliable way to handle relative imports across various modules. By including a default pathing block at the top of the main programs, we ensure that all relative imports are correctly resolved, preventing potential import errors.

## Default Pathing Block
To maintain consistent relative imports, we include the following default pathing block at the top of our main programs:

```
import os
import sys

cwd = os.getcwd()
if "HusseinLab_UltrafastPlasmaScience" not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")
# Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience', prevent import errors
cwd = os.path.sep.join(
    cwd.split(os.path.sep)[: cwd.split(os.path.sep).index("HusseinLab_UltrafastPlasmaScience") + 1]
)
sys.path.insert(0, cwd)
```

# Contributing
* Branches
	* Branches must change  or implement one feature
	* Branches created from branches must be merged in the order they are created
* Branch Naming
	* Branches are named as follows: <name_of_author>/<branch_type>/<description_of_branch>
	* Branch types may be one of the following: {hotfix,bugfix,experimental,feature}
* Commit Messages
	* __Do not assume your code is self explanatory__
	* __Do not assume everyone else knows what you are working on__
	* Use the imperative mood in the subject line
	* When in doubt, use the KISS method: Keep It Simple, Silly

## Converting PyQt5 Designer Files
To convert PyQt5 Designer `.ui` files to Python `.py` files that can be imported into your software, you can use the `pyuic5` tool. This tool is part of the PyQt5 package and allows you to generate Python code from the `.ui` files created using the Qt Designer.

### Command
The basic command to convert a `.ui` file to a `.py` file is:

```
pyuic5 -x ui_file.ui -o out_file.py
```
