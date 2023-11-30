# Newport XPS

This module provides code necessary to interface with Newport XPS controller using Python.

The framework for this class is built upon the SDK interface is developed in the Python module [newportxps](https://github.com/pyepics/newportxps). The code communicates with the XPS through "Actuator" objects, which are individual actuators connected to the XPS through the DRV slots.

As an example, connecting to and reading the status of an XPS Actuator may look like:
```python
from XPS import XPS

xps = XPS()
```

Also provided is an SOP for working with the XPS hardware, and an example Python GUI written in [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro), a Python wrapper for the Qt application framework. The GUI was designed using the [Qt designer](https://doc.qt.io/qt-5/qtdesigner-manual.html) program bundled with Anaconda installation. The GUI enables interfacing with a single XPS stage.
