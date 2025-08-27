import ctypes
import os
from enum import IntEnum
from typing import Union

# Convert error codes to messages
error_messages = {
    1: "No device was found",
    2: "A spectrometer was found but it is currently connected to another process",
    3: "Spectrometer has been disconnected",
    4: "Spectrometer is busy",
    5: "You have tried Read/Write to a register that does not exist",
    6: "The attempted operation is not supported by the connected DISB-board",
    7: "The entered parameter was out of bounds in terms of input range",
    8: "A high number of HW averages has been chosen - You may experience overflow of the 32-bit summation register",
    9: "SPI trigger is not enabled",
    10: "The spectrometer has timed out",
    11: "Other error",
    12: "The selected spectrum buffer is too small",
    13: "The entered production password is not correct",
    14: "The entered programming password is not correct",
    15: "The provided firmware file is not of the right format",
    16: "There is either no device connected that matches the given serial number or the device matching the serial number is currently connected to another process",
    17: "There are no linearity coefficients available for this spectrometer",
    18: "There is no thermistor connected to the DISB electronics board",
    19: "The DISB board only supports number of HW averages which are a power of 2 --> (1, 2, 4, 8, 16 ...)",
    20: "There is no connection to the spectrometer DISB board. Make sure that the DISB board is securely connected to the DISB-USB board."
}


# Enums
class CtypesEnum(IntEnum):
    """A ctypes-compatible IntEnum superclass."""
    @classmethod
    def from_param(cls, obj):
        return int(obj)

class SPECTROMETER_STATUS(CtypesEnum):
    SPECTROMETER_OK = 0
    SPECTROMETER_NO_DEVICE_FOUND = 1
    SPECTROMETER_CONNECTION_BUSY = 2
    SPECTROMETER_NOT_CONNECTED = 3
    SPECTROMETER_BUSY = 4
    SPECTROMETER_NONE_VALID_REGISTER_SELECTED = 5
    SPECTROMETER_NOT_SUPPORTED_BY_DISB_VERSION = 6
    SPECTROMETER_PARAMATER_OUT_OF_BOUND = 7
    SPECTROMETER_WARNING_POSSIBLE_HW_AVERAGE_OVERFLOW = 8
    SPECTROMETER_SPI_TRIGGER_NOT_ENABLED = 9
    SPECTROMETER_TIMEOUT = 10
    SPECTROMETER_OTHER_ERROR = 11
    SPECTROMETER_BUFFER_TOO_SMALL = 12
    SPECTROMETER_WRONG_PRODUCTION_PASSWORD = 13
    SPECTROMETER_WRONG_PROGRAMMING_PASSWORD = 14
    SPECTROMETER_WRONG_FIRMWARE_FORMAT = 15
    SPECTROMETER_SERIAL_NUMBER_NOT_FOUND = 16
    SPECTROMETER_NO_LINEARITY_COEFS = 17
    SPECTROMETER_THERMISTOR_NOT_CONNECTED = 18
    SPECTROMETER_HW_AVG_POWER_2 = 19
    SPECTROMETER_NO_DISB_CONNECTION = 20
    
class DISB(CtypesEnum):
    DISB101 = 0
    DISB101T = 1
    DISB105 = 2
    DISB315 = 3
    DISB380 = 4
    DISB386 = 5
    DISB400 = 6
    DISB411 = 7
    DISB415 = 8
    DISB466 = 9
    DISB485 = 10

    UNKNOWN_DISB = 1000

class DetectorType(CtypesEnum):
    CMOS = 0
    BT_CCD_Linear = 1
    BT_CCD_Area = 2
    BT_CCD_Area_TEC = 3
    InGaAs = 4
    InGaAs_Compact = 5
    InGaAs_Speed = 6
    InGaAs_TEC = 7
    NMOS = 8

    UNKNOWN_DETECTOR = 1000

class Firmware(CtypesEnum):
    isb1_v0_r11 = 0	# DISB-101
    isb1_v0_r12 = 1
    isb1_v0_r13 = 2
    isb1_v0_r14 = 3
    isb1_v0_r15 = 4
    isb1_v3_r11 = 5

    isb1_v1_r4 = 6		# DISB-101S, 101T and 105.
    isb1_v1_r5 = 7
    isb1_v1_r6 = 8
    isb1_v1_r7 = 9
    isb1_v1_r8 = 10
    isb1_v1_r9 = 11
    isb1_v1_r10 = 12

    isb3_v0_r12 = 13	# DISB-380
    isb3_v0_r13 = 14
    isb3_v0_r14 = 15
    isb3_v0_r15 = 16
    isb3_v0_r16 = 17
    isb3_v1_r12 = 18
    isb3_v1_r13 = 19

    isb4_v0_r1 = 20		# DISB-411 and DISB-415
    isb4_v0_r2 = 21
    isb4_v0_r3 = 22
    isb4_v0_r4 = 23
    isb4_v0_r5 = 24

    isb5_v0_r1 = 25		# DISB-315
    isb5_v0_r2 = 26
    isb5_v0_r3 = 27

    isb5_v1_r1 = 28		# DISB-315-2D
    isb5_v1_r2 = 29
    isb5_v1_r3 = 30
    isb5_v1_r4 = 31
    isb5_v2_r2 = 32
    isb5_v2_r3 = 33

    isb6_v0_r1 = 34		# DISB-400
    isb6_v0_r2 = 35
    isb6_v0_r3 = 36
    isb6_v0_r4 = 37
    isb6_v0_r5 = 38

    isb7_v0_r1 = 39		# DISB-466
    isb7_v0_r2 = 40
    isb7_v0_r3 = 41
    isb7_v0_r4 = 42
    isb7_v0_r5 = 43

    isb8_v0_r1 = 44     # DISB-385
    isb8_v0_r2 = 45
    isb8_v0_r3 = 46
    isb8_v0_r4 = 47
    isb8_v0_r5 = 48

    isb9_v0_r1 = 49     # DISB-386
    isb9_v0_r2 = 50
    isb9_v0_r3 = 51
    isb9_v0_r4 = 52
    isb9_v0_r5 = 53

    UNKNOWN_FIRMWARE = 1000

class AUX_OUTPUT_MODE(CtypesEnum):
    ALWAYS_OFF = 0
    ALWAYS_ON = 1
    STROBING_FOR_SET_TIME_DURATION = 2
    ON_FOR_SET_TIME_DURATION = 3

class TEMPERATURE_FORMAT(CtypesEnum):
    CELCIUS = 0
    FAHRENHEIT = 1
    ADC_12BIT = 2

class GAIN_MODE(CtypesEnum):
    LOW = 0
    HIGH = 1

# Structs
class WavelengthCalibration(ctypes.Structure):
    '''Attributes:

    Coefficient_0 (float)
    
    Coefficient_1 (float)
    
    Coefficient_2 (float)
    
    Coefficient_3 (float)
    
    Coefficient_4 (float)
    
    Coefficient_5 (float)
    '''
    _fields_ = [("Coefficient_0", ctypes.c_double),
               ("Coefficient_1", ctypes.c_double),
               ("Coefficient_2", ctypes.c_double),
               ("Coefficient_3", ctypes.c_double),
               ("Coefficient_4", ctypes.c_double),
               ("Coefficient_5", ctypes.c_double)]
    
    def __str__(self) -> str:
        ret_str = []
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("{0}: {1}".format(attr, value))
        return ', '.join(ret_str)

class LinearityCalibration(ctypes.Structure):
    '''Attributes:

    Coefficient_0 (float)
    
    Coefficient_1 (float)
    
    Coefficient_2 (float)
    
    Coefficient_3 (float)
    
    Coefficient_4 (float)
    
    Coefficient_5 (float)

    Coefficient_6 (float)
    
    Coefficient_7 (float)
    '''
    _fields_ = [("Coefficient_0", ctypes.c_double),
               ("Coefficient_1", ctypes.c_double),
               ("Coefficient_2", ctypes.c_double),
               ("Coefficient_3", ctypes.c_double),
               ("Coefficient_4", ctypes.c_double),
               ("Coefficient_5", ctypes.c_double),
               ("Coefficient_6", ctypes.c_double),
               ("Coefficient_7", ctypes.c_double)]
    
    def __str__(self) -> str:
        ret_str = []
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("{0}: {1}".format(attr, value))
        return ', '.join(ret_str)

class Information(ctypes.Structure):
    '''Attributes:
    
    DISB_PCB_SerialNumber (ctypes.c_uint)
    
    Spectrometer_SerialNumber (ctypes.c_uint)
    
    Electronics_Variant (DISB enum)
    
    Electronics_Revision (ctypes.c_ushort)
    
    Detector_Type (DetectorType enum)
    
    Firmware (Firmware enum)
    
    WavelengthCoefficients (WavelengthCalibration struct)
    
    LinearityCoefficients (LinearityCalibration enum)
    
    NumberDetectorPixels (ctypes.c_ushort)'''
    _fields_ = [("DISB_PCB_SerialNumber", ctypes.c_uint),
                ("Spectrometer_SerialNumber", ctypes.c_uint),
                ("Electronics_Variant", ctypes.c_int),
                ("Electronics_Revision", ctypes.c_ushort),
                ("Detector_Type", ctypes.c_int),
                ("Firmware", ctypes.c_int),
                ("WavelengthCoefficients", WavelengthCalibration),
                ("LinearityCoefficients", LinearityCalibration),
                ("NumberDetectorPixels", ctypes.c_ushort)]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append("Spectrometer " + str(self.__class__.__name__) + ':')
        for field in self._fields_:
            attr, _ = field

            if attr == "Electronics_Variant":
                value = DISB(getattr(self, attr))._name_
            elif attr == "Detector_Type":
                value = DetectorType(getattr(self, attr))._name_
            elif attr == "Firmware":
                value = Firmware(getattr(self, attr))._name_
            else:
                value = getattr(self, attr)

            ret_str.append("\t {0}: {1}".format(attr, value))
        return '\n'.join(ret_str)

class GPIO_input(ctypes.Structure):
    '''Attributes:
    
    pin_0 (bool)
    
    pin_1 (bool)
    
    pin_2 (bool)'''
    _fields_ = [("pin_0", ctypes.c_bool),
                ("pin_1", ctypes.c_bool),
                ("pin_2", ctypes.c_bool)]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append(str(self.__class__.__name__) + ':')

        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("\t {0}: {1}".format(attr, value))
        
        return '\n'.join(ret_str)

class GPIO_output(ctypes.Structure):
    '''Attributes:
    
    pin_0 (bool)

    pin_1 (bool)

    pin_2 (bool)
    '''
    _fields_ = [("pin_0", ctypes.c_bool),
                ("pin_1", ctypes.c_bool),
                ("pin_2", ctypes.c_bool)]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append(str(self.__class__.__name__) + ':')
        
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("\t {0}: {1}".format(attr, value))
        
        return '\n'.join(ret_str)

class HW_AVERAGING_STATUS(ctypes.Structure):
    '''Attributes:
    
    AUTO_TRIG (bool)

    INPROGRESS (bool)
    '''
    _fields_ = [("AUTO_TRIG", ctypes.c_bool),
                ("INPROGRESS", ctypes.c_bool)]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append(str(self.__class__.__name__) + ':')
        
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("\t {0}: {1}".format(attr, value))
        
        return '\n'.join(ret_str)

class Trigger_mode(ctypes.Structure):
    '''Attributes:
    
    SPI_trigger_enabled (bool)

    ExternalHW_trigger_enabled (bool)

    Internal_trigger_enabled(bool)
    '''
    _fields_ = [("SPI_trigger_enabled", ctypes.c_bool),
                ("ExternalHW_trigger_enabled", ctypes.c_bool),
                ("Internal_trigger_enabled", ctypes.c_bool)]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append(str(self.__class__.__name__) + ':')
        
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("\t {0}: {1}".format(attr, value))
        
        return '\n'.join(ret_str)

class TEC_Settings(ctypes.Structure):
    '''Attributes:

    Enable_TEC (bool)

    Manual_Control_Mode (bool)
    '''
    _fields_ = [("Enable_TEC", ctypes.c_bool),
                ("Manual_Control_Mode", ctypes.c_bool)]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append(str(self.__class__.__name__) + ':')
        
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("\t {0}: {1}".format(attr, value))
        
        return '\n'.join(ret_str)

class PID_Coefficients(ctypes.Structure):
    '''Attributes:
    
    P (int)

    I (int)

    D (int)

    K (int)
    '''
    _fields_ = [("P", ctypes.c_ushort),
                ("I", ctypes.c_ushort),
                ("D", ctypes.c_ushort),
                ("K", ctypes.c_ushort),]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append(str(self.__class__.__name__) + ':')
        
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("\t {0}: {1}".format(attr, value))
        
        return '\n'.join(ret_str)

class TEC_Status(ctypes.Structure):
    '''Attributes
    
    Temperature_Above_50_Deg_Celcius (bool)

    Temperature_Not_Stable (bool)
    '''
    _fields_ = [("Temperature_Above_50_Deg_Celcius", ctypes.c_bool),
                ("Temperature_Not_Stable", ctypes.c_bool)]
    
    def __str__(self) -> str:
        ret_str = []
        ret_str.append(str(self.__class__.__name__) + ':')
        
        for field in self._fields_:
            attr, _ = field
            value = getattr(self, attr)
            ret_str.append("\t {0}: {1}".format(attr, value))
        
        return '\n'.join(ret_str)

# Import DLL functions
ibsen_lib = ctypes.cdll.LoadLibrary(os.path.dirname(os.path.realpath(__file__)) + '/DISB_SDK_LIBRARY-x64.dll')

# Get version of the SDK
def GetDLLversion() -> tuple[int, int, int]:
    '''Print the version number of the current DLL driver for the spectrometer
    
    Please supply this information when contacting Ibsen Photonics regarding issues with the SDK'''
    major = ctypes.c_ushort(0)
    minor = ctypes.c_ushort(0)
    patch = ctypes.c_ushort(0)

    ibsen_lib.GetDLLversion(ctypes.byref(major), ctypes.byref(minor), ctypes.byref(patch))

    return (major.value, minor.value, patch.value)

# Get Available spectrometers
def SpectrometersAvailable() -> list[str]:
    '''Returns a list of strings describing the serial numbers of all currently available spectrometers'''
    num_specs = ctypes.c_ushort(0)

    status = ibsen_lib.IBSEN_NumberOfSpectrometersAvailable(ctypes.byref(num_specs))

    # Throw error if not SPECTROMETER_OK
    if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
        raise Exception(error_messages[status])
    
    if num_specs == 0:
        raise Exception(error_messages[SPECTROMETER_STATUS.SPECTROMETER_NO_DEVICE_FOUND]) 
    
    spec_list = []

    for i in range(num_specs.value):
        try:
            spec = SPECTROMETER(i)
            spec_list.append(str(spec.m_info.Spectrometer_SerialNumber))
        except:
            pass
    
    if len(spec_list) == 0:
        raise Exception(error_messages[SPECTROMETER_STATUS.SPECTROMETER_NO_DISB_CONNECTION])
    
    return spec_list

# Spectrometer class
class SPECTROMETER():

    def __init__(self, id : Union[str,int]):
        '''Connect to a spectrometer using the serial number or the device manager index of the spectrometer'''
        self.m_timeout_seconds = 10.0 # The time limit a spectral measurement can go on for before returning an error
        self.m_info = None # Struct containing all information regarding the spectrometer

        self._m_reg = None
        self._m_stream = None
        self._m_anyDevicesAvailable = None
        self._m_single_spectrum_buffer_size = None

        if isinstance(id, str):
            serial_number = id.encode('utf-8')
            regHandle = ctypes.c_void_p(0)
            streamHandle = ctypes.c_void_p(0)
            anyDevicesAvailable = ctypes.c_bool(0)
            neededSpectralBufferSize = ctypes.c_ushort(0)
            info = Information()

            ibsen_lib.IBSEN_initSpectrometer_serial_number(serial_number, ctypes.byref(regHandle),
                                                           ctypes.byref(streamHandle), ctypes.byref(anyDevicesAvailable),
                                                           ctypes.byref(neededSpectralBufferSize), ctypes.byref(info))
            
            status = ibsen_lib.IBSEN_isSpectrometerConnected(regHandle, streamHandle, anyDevicesAvailable)

            # Throw error if not SPECTROMETER_OK
            if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
                raise Exception(error_messages[status])

            self.m_info = info
            self._m_reg = regHandle
            self._m_stream = streamHandle
            self._m_anyDevicesAvailable = anyDevicesAvailable
            self._m_single_spectrum_buffer_size = neededSpectralBufferSize

        else:
            spec_num = ctypes.c_uint(id)
            regHandle = ctypes.c_void_p(0)
            streamHandle = ctypes.c_void_p(0)
            anyDevicesAvailable = ctypes.c_bool(0)
            neededSpectralBufferSize = ctypes.c_ushort(0)
            info = Information()

            ibsen_lib.IBSEN_initSpectrometer(spec_num, ctypes.byref(regHandle), ctypes.byref(streamHandle),
                                             ctypes.byref(anyDevicesAvailable), ctypes.byref(neededSpectralBufferSize),
                                             ctypes.byref(info))

            status = ibsen_lib.IBSEN_isSpectrometerConnected(regHandle, streamHandle, anyDevicesAvailable)

            # Throw error if not SPECTROMETER_OK
            if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
                raise Exception(error_messages[status])

            self.m_info = info
            self._m_reg = regHandle
            self._m_stream = streamHandle
            self._m_anyDevicesAvailable = anyDevicesAvailable
            self._m_single_spectrum_buffer_size = neededSpectralBufferSize
        
        # Force update m_timeout_seconds via SetExposureTime
        exp_time = ctypes.c_double()

        status = ibsen_lib.IBSEN_GetExposureTime(self._m_reg, ctypes.byref(exp_time))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        exp_time = exp_time.value

        newExpTime_ms = ctypes.c_double(exp_time)
        timeout_seconds = ctypes.c_double()

        status = ibsen_lib.IBSEN_SetExposureTime(self._m_reg, newExpTime_ms, ctypes.byref(timeout_seconds))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        self.m_timeout_seconds = timeout_seconds.value

    # Spectrometer information ------------------------------------------------------
    def GetWavelengthAxis(self) -> list[float]:
        '''Get the wavlength axis of current data returned from the spectrometer, given the currently set ROI

        The unit of the returned data is nm.
        '''
        wav_axis = (ctypes.c_double * self._m_single_spectrum_buffer_size.value)()

        _, _, pix_start, pix_end = self.GetRegionOfInterest()

        status = ibsen_lib.IBSEN_GetWavelengthAxis(self._m_reg, ctypes.byref(wav_axis), ctypes.c_ushort(pix_start), ctypes.c_ushort(pix_end))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return list(wav_axis)

    def GetWavenumberAxis(self, laser_wavelength_nm : float) -> list[float]:
        '''Get the wavenumber axis of data returned from the spectrometer, given the currently set ROI.
        
        The unit of the returned data is cm^-1.
        '''
        wn_axis = (ctypes.c_double * self._m_single_spectrum_buffer_size.value)()

        _, _, pix_start, pix_end = self.GetRegionOfInterest()

        status = ibsen_lib.IBSEN_GetWavenumberAxis(self._m_reg, ctypes.byref(wn_axis), ctypes.c_double(laser_wavelength_nm), ctypes.c_ushort(pix_start), ctypes.c_ushort(pix_end))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return list(wn_axis)

    def GetTriggerLockout(self) -> bool:
        '''Get the status of the trigger lockout of the spectrometer'''
        lockout_status = ctypes.c_bool()

        status = ibsen_lib.IBSEN_GetTriggerLockout(self._m_reg, ctypes.byref(lockout_status))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

        return lockout_status.value

    # Manual spectrum acquisition ---------------------------------------------------
    def ResetSpectrumBuffer(self):
        '''Reset the image transfer buffer on the DISB electronics.
        
        If the Internal trigger of the spectrometer is enabled, this function can be used as an alternative to StartExposure when doing manual spectrum acquisition.
        '''
        status = ibsen_lib.IBSEN_ResetSpectrumBuffer(self._m_reg)

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def AbortCurrentExposure(self):
        '''Aborts the current spectrum measurement and resets the image transfer buffer on the DISB electronics.
        
        This function can be used to stop a detector exposure before it finished the exposure period.
        This can be useful if very long exposure times are used and the user wants a measurement to end immediately.
        
        Please note that this function also turns off the internal trigger of the board and sets the detector gain mode to LOW, if applicable.
        '''
        status = ibsen_lib.IBSEN_AbortCurrentExposure(self._m_reg)

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def StartExposure(self):
        '''Starts a spectral measurement using an exposure time stored in the DISB electronics.
        
        Before starting an exposure, this function will abort any current exposure and clear the image transfer buffer.
        
        Please note that this function only triggers the spectrometer to start an exposure of the detector if internal triggering or SPi trigger is enabled.
        If only HW triggering is enabled, this function does nothing more than aborting any current measurement and clearing the image transfer buffer. 
        '''
        status = ibsen_lib.IBSEN_StartExposure(self._m_reg)

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def IsDataReady(self) -> bool:
        '''Checks if there is any spectral data ready to be transfered from the DISB electronics.'''
        is_data_ready = ctypes.c_bool()
        status = ibsen_lib.IBSEN_IsDataReady(self._m_reg, ctypes.byref(is_data_ready))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return is_data_ready.value
    
    def ReadSpectrumBuffer(self) -> list[int]:
        '''Retrieves the spectral data present in the DISB electronics image transfer buffer.
        
        If this function has been called without starting an exposure of the detector, the spectral ADC values will all be 0.
        '''
        spectrum = (ctypes.c_ushort * self._m_single_spectrum_buffer_size.value)()

        status = ibsen_lib.IBSEN_ReadSpectrumBuffer(self._m_reg, self._m_stream, ctypes.byref(spectrum),
                                                    self._m_single_spectrum_buffer_size, ctypes.c_double(self.m_timeout_seconds))
        
        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return list(spectrum)

    # Automatic spectrum acquisition -------------------------------------------
    def GetSingleSpectrum(self) -> list[int]:
        '''Starts a spectrometer measurement using the exposure time stored in the DISB electronics.
        
        When the measurement is finished the function returns the spectrum as a list of ints.

        This function will only return if a trigger signal has been given to the DISB electronics after this function has been called.
        
        The trigger can be either internal, external or SPI-based. These trigger conditions can be set using the SetTriggerMode function.
        '''
        spectrum = (ctypes.c_ushort * self._m_single_spectrum_buffer_size.value)()

        status = ibsen_lib.IBSEN_GetSingleSpectrum(self._m_reg, self._m_stream, ctypes.byref(spectrum),
                                                   self._m_single_spectrum_buffer_size, ctypes.c_double(self.m_timeout_seconds))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return list(spectrum)

    def GetSingleSpectrum_LinearityCorrected(self) -> list[int]:
        '''Does the same as GetSingleSpectrum, but this function applies the linearity coefficients of the spectrometer, if they are present, to the spectrum retrieved from the spectrometer.'''
        spectrum = (ctypes.c_uint * self._m_single_spectrum_buffer_size.value)()

        status = ibsen_lib.IBSEN_GetSingleSpectrum_LinearityCorrected(self._m_reg, self._m_stream, ctypes.byref(spectrum),
                                                                      self._m_single_spectrum_buffer_size, ctypes.c_double(self.m_timeout_seconds))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return list(spectrum)

    def GetMultipleSpectra(self, num_of_spectra : int) -> tuple[list[list[int]], list[float]]:
        '''Retrieves data from several spectral measurements in a row, where the number of spectra taken is user defined.
        
        Using this function will retrieve the spectra in the quickest way possible, given that a trigger signal is always present.

        This function also returns an array of elapsed time since the first measurement in the series was started, given in microseconds.
        This can be used to determine the datetime of each individual measurement in the series.

        Input:
            num_of_spectra(int): Number of spectra to be taken
        
        Output:
            multiple_spectra(list(list)): 2D list containging num_of_spectra measurements, where each measurement is a row in the 2D list
            elapsed_time_us(list): Time elapsed between calling the function and each spectrum being returned
        '''
        spectrum = (ctypes.c_ushort * (self._m_single_spectrum_buffer_size.value * num_of_spectra))()
        elapsed_time = (ctypes.c_uint * num_of_spectra)()

        status = ibsen_lib.IBSEN_GetMultipleSpectra(self._m_reg, self._m_stream, ctypes.byref(spectrum),
                                                    ctypes.byref(elapsed_time), ctypes.c_ushort(num_of_spectra),
                                                    self._m_single_spectrum_buffer_size, ctypes.c_double(self.m_timeout_seconds))
        
        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        spectrum = list(spectrum)
        
        # 2D list
        index = 0
        spectrum_2D = [[] for _ in range(num_of_spectra)]
        for i in range(num_of_spectra):
            for _ in range(self._m_single_spectrum_buffer_size.value):
                spectrum_2D[i].append(spectrum[index])
                index += 1

        return spectrum_2D, list(elapsed_time)

    def GetAveragedSpectrum(self, numOfAverages : int) -> list[float]:
        '''Returns an averaged spectrum based on a user defined number of averages.
        
        Please note that these averages are done after the spectral data has been received from the DISB electronics.
        Spectral averaging can additionally be done directly on the DISB electronics hardware, by using the SetNumberHWaveraging function.

        If the HW averaging Auto-Trigger in the HWaveragingControl has been set to FALSE for the spectrometer,
        GetAveragedSpectrum will only function correctly if the Internal Trigger of the spectrometer has been enabled or if an external trigger is
        utilized while the External HW trigger mode has been enabled.
        '''
        spectrum = (ctypes.c_double * self._m_single_spectrum_buffer_size.value)()

        status = ibsen_lib.IBSEN_GetAveragedSpectrum(self._m_reg, self._m_stream, ctypes.byref(spectrum), ctypes.c_ushort(numOfAverages),
                                                   self._m_single_spectrum_buffer_size, ctypes.c_double(self.m_timeout_seconds))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return list(spectrum)

    # Exposure time -----------------------------------------------------------------
    def SetExposureTime(self, newExpTime_ms : float):
        '''Sets the exposure time of the detector during a spectrometer measurement, rounded to the nearest possible setting.
        
        The unit for the input parameter is milliseconds.
        '''
        exp_time = ctypes.c_double(newExpTime_ms)
        timeout_seconds = ctypes.c_double()

        status = ibsen_lib.IBSEN_SetExposureTime(self._m_reg, exp_time, ctypes.byref(timeout_seconds))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        self.m_timeout_seconds = timeout_seconds.value

    def GetExposureTime(self) -> float:
        '''Returns the value of the exposure time set in the DISB electronics, given in milliseconds.'''
        exp_time = ctypes.c_double()

        status = ibsen_lib.IBSEN_GetExposureTime(self._m_reg, ctypes.byref(exp_time))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return exp_time.value
    
    # MPP control -------------------------------------------------------------------
    def SetTimeToEnableMPP(self, mpp_time_ms : float):
        '''Sets the exposure time limit of where the CCD detector starts operating in MPP mode, if it is capapble of doing so.
        
        The unit for the input is in milliseconds.
        '''
        status = ibsen_lib.SetTimeToEnableMPP(self._m_reg, ctypes.c_double(mpp_time_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
    def GetTimeToEnableMPP(self) -> float:
        '''Gets the exposure time limit of where the CCD detector starts operating in MPP mode, if it is capapble of doing so.
        
        The unit of the output is in milliseconds.'''
        mpp_time_ms = ctypes.c_double()

        status = ibsen_lib.IBSEN_GetTimeToEnableMPP(self._m_reg, ctypes.byref(mpp_time_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return mpp_time_ms.value

    # Hardware averages -------------------------------------------------------------
    def SetNumberHWaveraging(self, num_of_HW_averages : int):
        '''Sets the number of spectrum averages the DISB electronics are doing before transfering the spectral data.
        
        Setting the number of HW averages to 1 disables this feature.

        The user can control whether the DISB electronics are to do the averages as fast as possible using
        automatic triggering or if the DISB electronics should wait for a trigger each measurement during the averaging process.
        This behaviour can be set using the SetHWaveragingControl function.
        '''
        timeout_seconds = ctypes.c_double(self.m_timeout_seconds)
        
        status = ibsen_lib.IBSEN_SetNumberHWaveraging(self._m_reg, ctypes.c_ushort(num_of_HW_averages), ctypes.byref(timeout_seconds))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

        self.m_timeout_seconds = timeout_seconds.value

    def GetNumberHWaveraging(self) -> int:
        '''Returns the number of spectral averages that is done on the DISB electronics before a spectrum is transfered.
        
        A returned value of 1 means that the feature is disabled.
        '''
        num_hw_avg = ctypes.c_ushort()

        status = ibsen_lib.IBSEN_GetNumberHWaveraging(self._m_reg, ctypes.byref(num_hw_avg))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return num_hw_avg.value

    def SetHWaveragingControl(self, enable_auto_trig : bool):
        '''Controls whether the DISB electronics spectral averaging feature is taking averages as fast as possible using
        automatic triggering between each measurement in the averaging series or if it waits for a user-defined trigger
        between each measurement in the series.
        '''
        status = ibsen_lib.IBSEN_SetHWaveragingControl(self._m_reg, ctypes.c_bool(enable_auto_trig))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetHWaveragingControl(self) -> HW_AVERAGING_STATUS:
        '''Returns the status of the DISB electronics on-board spectral averaging feature.
        
        The returned status contains the state of the auto trigger feature, as described in SetNumberHWaveraging function,
        and if the DISB electronics are currently in the middle of an averaging measurement.
        '''
        hw_avg_status = HW_AVERAGING_STATUS()

        status = ibsen_lib.IBSEN_GetHWaveragingControl(self._m_reg, ctypes.byref(hw_avg_status))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return hw_avg_status

    # Trigger control ---------------------------------------------------------------
    def SetTriggerMode(self, trigger_mode : Trigger_mode):
        '''Sets which trigger options are able to start a spectral measurement.'''
        status = ibsen_lib.IBSEN_SetTriggerMode(self._m_reg, trigger_mode)

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetTriggerMode(self) -> Trigger_mode:
        '''Returns which trigger options are able to start a spectral measurement.'''
        trigger_mode = Trigger_mode()

        status = ibsen_lib.IBSEN_GetTriggerMode(self._m_reg, ctypes.byref(trigger_mode))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return trigger_mode
    
    def SetTriggerDelay(self, trig_delay_ms : float):
        '''If the input to this function is positive, the trigger delay is setting the delay between when
        the trigger is received by the DISB electronics and the exposure of the detector starts.
        
        If the input is negative, the trigger delay controls the delay between the trigger and the start of the AUX0 signal.

        The unit for the input parameter is in milliseconds.

        For more information, please see the Triggering section of the DISB electronics hardware manual.
        '''
        status = ibsen_lib.IBSEN_SetTriggerDelay(self._m_reg, ctypes.c_double(trig_delay_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def GetTriggerDelay(self) -> float:
        '''If the output to this function is positive, the trigger delay returned is the delay between when the trigger is received by the DISB electronics and the exposure of the detector starts.
        
        If the output is negative, the trigger delay returned is the the delay between the trigger and the start of the AUX0 signal.

        The returned value has the unit of milliseconds.

        For more information, please see the Triggering section of the DISB electronics hardware manual.
        '''
        trig_delay_ms = ctypes.c_double()

        status = ibsen_lib.IBSEN_GetTriggerDelay(self._m_reg, ctypes.byref(trig_delay_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return trig_delay_ms.value
    
    def SetInternalTriggerPulsePeriod(self, itpp : float):
        '''Sets the internal trigger pulse period(ITPP) in units of milliseconds.
        
        The pulse period can be set in steps of 50 µs and it will therefore round any input to the closest mulitple of 50 µs.
        '''
        status = ibsen_lib.IBSEN_SetInternalTriggerPulsePeriod(self._m_reg, ctypes.c_double(itpp))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def GetInternalTriggerPulsePeriod(self) -> float:
        '''Gets the internal trigger pulse period(ITPP) in units of milliseconds.'''
        itpp = ctypes.c_double()

        status = ibsen_lib.IBSEN_GetInternalTriggerPulsePeriod(self._m_reg, ctypes.byref(itpp))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

        return itpp.value

    # AUX control -------------------------------------------------------------------
    def SetAUXmode(self, aux_mode : AUX_OUTPUT_MODE):
        '''Sets the operation mode for the AUX0 output of the DISB electronics.
        
        For more information regarding the behaviour of the different AUX 0 modes, please see the Triggering section
        of the DISB electronics hardware manual.
        '''
        status = ibsen_lib.IBSEN_SetAUXmode(self._m_reg, ctypes.c_int(aux_mode))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetAUXmode(self) -> AUX_OUTPUT_MODE:
        '''Returns the operation mode for the AUX0 output of the DISB electronics.
        
        For more information regarding the behaviour of the different AUX 0 modes, please see the Triggering section of the DISB electronics hardware manual.
        '''
        aux_mode = ctypes.c_int()

        status = ibsen_lib.IBSEN_GetAUXmode(self._m_reg, ctypes.byref(aux_mode))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return AUX_OUTPUT_MODE(aux_mode.value)

    def SetAUXduration(self, aux_dur_ms : float):
        '''Sets the duration of the AUX0 signal being active, given in milliseconds.
        
        For more information about the AUX0 signal, please refer to the DISB electronics hardware manual.
        '''
        status = ibsen_lib.IBSEN_SetAUXduration(self._m_reg, ctypes.c_double(aux_dur_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetAUXduration(self) -> float:
        '''Returns the duration of the AUX0 signal being active, given in milliseconds.
        
        For more information about the AUX0 signal, please refer to the DISB electronics hardware manual.'''
        aux_dur_ms = ctypes.c_double()

        status = ibsen_lib.IBSEN_GetAUXduration(self._m_reg, ctypes.byref(aux_dur_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return aux_dur_ms.value

    def SetAUXstrobeInterval(self, aux_strobe_interval_ms : float):
        '''Sets the duration of the AUX0 strobe duration when operated in the mode STROBING_FOR_SET_TIME_DURATION. given in milliseconds.
        
        The input is rounded to the nearest multiple of 50 µs.

        For more information on the operation of AUX0, please refer to the DISB electronics hardware manual.
        '''
        status = ibsen_lib.IBSEN_SetAUXstrobeInterval(self._m_reg, ctypes.c_double(aux_strobe_interval_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def GetAUXstrobeInterval(self) -> float:
        '''Returns the duration of the AUX0 strobe duration when operated in the mode STROBING_FOR_SET_TIME_DURATION. given in milliseconds.
        
        For more information on the operation of AUX0, please refer to the DISB electronics hardware manual.'''
        aux_strobe_interval_ms = ctypes.c_double()

        status = ibsen_lib.IBSEN_GetAUXstrobeInterval(self._m_reg, ctypes.byref(aux_strobe_interval_ms))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return aux_strobe_interval_ms.value

    # GPIO --------------------------------------------------------------------------
    def SetGPIOoutputPinStatus(self, output_pin_status : GPIO_output):
        '''Sets the state of the available GPIO Output pins on the DISB electronics.
        
        For more information regarding the GPIO pins, please refer to the GPIO-section of the DISB electronics hardware manual.'''
        status = ibsen_lib.IBSEN_SetGPIOoutputPinStatus(self._m_reg, output_pin_status)

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetGPIOoutputPinStatus(self) -> GPIO_output:
        '''Returns the state of the available GPIO Output pins on the DISB electronics.
        
        For more information regarding the GPIO pins, please refer to the GPIO-section of the DISB electronics hardware manual.'''
        output_pin_status = GPIO_output()

        status = ibsen_lib.IBSEN_GetGPIOoutputPinStatus(self._m_reg, ctypes.byref(output_pin_status))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return output_pin_status

    def GetGPIOinputPinStatus(self) -> GPIO_input:
        '''Gets the state of the available GPIO Input pins on the DISB electronics.
        
        For more information regarding the GPIO pins, please refer to the GPIO-section of the DISB electronics hardware manual.'''
        input_pin_status = GPIO_input()

        status = ibsen_lib.IBSEN_GetGPIOinputPinStatus(self._m_reg, ctypes.byref(input_pin_status))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return input_pin_status

    # Region of interest ------------------------------------------------------------
    def GetRegionOfInterest(self) -> tuple[float, float, int, int]:
        '''Returns the current region of interest for the connected spectrometer, given in both pixels and wavelength'''
        start_wavelength = ctypes.c_double()
        end_wavelength = ctypes.c_double()
        start_pixel = ctypes.c_int()
        end_pixel = ctypes.c_int()

        status = ibsen_lib.IBSEN_GetRegionOfInterest(self._m_reg, ctypes.byref(start_pixel), ctypes.byref(end_pixel),
                                                     ctypes.byref(self._m_single_spectrum_buffer_size))
        
        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        status = ibsen_lib.IBSEN_GetRegionOfInterest_Wavelength(self._m_reg, ctypes.byref(start_wavelength),
                                                                ctypes.byref(end_wavelength), ctypes.byref(self._m_single_spectrum_buffer_size))
        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return start_wavelength.value, end_wavelength.value, start_pixel.value, end_pixel.value
    
    def SetRegionOfInterest(self, starting_point : Union[float,int], end_point : Union[float, int]):
        '''Sets the region of interest for the connected spectrometer.
        
        If the input for this function is a set of int numbers, the input is interperted as (pix_start, pix_end)
        
        If the input is two floats, the input is interperted as (wl_start, wl_end)
        '''
        if isinstance(starting_point, float) and isinstance(end_point, float):

            status = ibsen_lib.IBSEN_SetRegionOfInterest_Wavelength(self._m_reg, ctypes.c_double(starting_point),
                                                                    ctypes.c_double(end_point),
                                                                    ctypes.byref(self._m_single_spectrum_buffer_size))
            
            # Throw error if not SPECTROMETER_OK
            if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
                raise Exception(error_messages[status])

        elif isinstance(starting_point, int) and isinstance(end_point, int):
            status = ibsen_lib.IBSEN_SetRegionOfInterest(self._m_reg, ctypes.c_ushort(starting_point), ctypes.c_ushort(end_point),
                                                        ctypes.byref(self._m_single_spectrum_buffer_size))
            
            # Throw error if not SPECTROMETER_OK
            if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
                raise Exception(error_messages[status])
        
        else:
            raise Exception("Mixed type input parameters provided - Please only provide one set of intergers for\
                            ROI in pixels or one set of floats in ROI is to be set in wavelength")

    # Wavelength calibration coefficients -------------------------------------------
    def SetWavelengthCalibration(self, wav_cal : WavelengthCalibration, prodPass : int):
        '''Sets the wavelength calibration coefficients stored on the DISB electronics.
        
        The coefficients are used to calculate the wavelength value of a given pixel and is used in the functions GetWavelengthAxis and Set/Get Region of Interest.

        This function requires a production password to overwrite the coefficients that comes with the spectrometer. Please contact Ibsen Photonics to acquire this password.
        '''
        status = ibsen_lib.IBSEN_SetWavelengthCalibration(self._m_reg, ctypes.byref(self.m_info), ctypes.c_ushort(prodPass),
                                                    ctypes.byref(wav_cal))
        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetWavelengthCalibration(self) -> WavelengthCalibration:
        '''Returns the wavelength axis of the spectrometer using the current pixel to wavelength calibration coefficients stored in the DISB electronics.
        
        The unit of the returned wavelengths is nm.'''
        wav_cal = WavelengthCalibration()

        status = ibsen_lib.IBSEN_GetWavelengthCalibration(self._m_reg, ctypes.byref(wav_cal))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return wav_cal

    # Linearity calibration coefficients --------------------------------------------
    def SetLinearityCalibration(self, lin_cal : LinearityCalibration, prodPass : int):
        '''Sets the pixel linearity coefficients stored in the DISB electronics.
        
        The coefficients are used to compensate for the non-linear nature of the pixel saturation profile and is used in the function GetSingleSpectrum_LinearityCorrected.

        This function requires a password to write new coefficients to the DISB electronics. The password can be required by contacting Ibsen Photonics.'''
        status = ibsen_lib.IBSEN_SetLinearityCalibration(self._m_reg, ctypes.byref(self.m_info), ctypes.c_ushort(prodPass),
                                                         ctypes.byref(lin_cal))
        
        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetLinearityCalibration(self) -> LinearityCalibration:
        '''Returns the pixel linearity coefficients stored in the DISB electronics.
        
        The coefficients are used to compensate for the non-linear nature of the pixel saturation profile and is used in the function GetSingleSpectrum_LinearityCorrected.'''
        lin_cal = LinearityCalibration()

        status = ibsen_lib.IBSEN_GetLinearityCalibration(self._m_reg, ctypes.byref(lin_cal))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return lin_cal
    
    # ADC Gain / Offset -------------------------------------------------------------
    def SetAdcGain(self, gain_factor : float):
        '''Sets the ADC gain factor of the DISB electronics.'''
        status = ibsen_lib.IBSEN_SetAdcGain(self._m_reg, ctypes.c_double(gain_factor))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetAdcGain(self) -> float:
        '''Returns the ADC gain factor of the DISB electronics.'''
        gain_factor = ctypes.c_double(0)

        status = ibsen_lib.IBSEN_GetAdcGain(self._m_reg, ctypes.byref(gain_factor))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return gain_factor.value
    
    def SetAdcOffset(self, adc_offset_mV : float):
        '''Sets the ADC Offset value of the DISB electronics, given in milli Volts.'''
        status = ibsen_lib.IBSEN_SetAdcOffset(self._m_reg, ctypes.c_double(adc_offset_mV))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetAdcOffset(self) -> float:
        '''Returns the ADC Offset value of the DISB electronics, given in milli Volts.'''
        adc_offset_mV = ctypes.c_double(0)

        status = ibsen_lib.IBSEN_GetAdcOffset(self._m_reg, ctypes.byref(adc_offset_mV))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return adc_offset_mV.value
    
    # Gain mode ---------------------------------------------------------------------
    def SetGainMode(self, gain_mode : GAIN_MODE):
        '''Sets the gain mode of the DISB electronics.
        
        Note that this function is only available for a small number of DISB variants.'''
        status = ibsen_lib.IBSEN_SetGainMode(self._m_reg, ctypes.c_int(gain_mode))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetGainMode(self) -> GAIN_MODE:
        '''Returns the gain mode of the DISB electronics.
        
        Note that this function is only available for a small number of DISB variants.'''
        gain_mode = ctypes.c_int(0)

        status = ibsen_lib.IBSEN_GetGainMode(self._m_reg, gain_mode)

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return GAIN_MODE(gain_mode.value)

    # Thermistor temperature --------------------------------------------------------
    def GetThermistorTemperature(self, temp_format : TEMPERATURE_FORMAT) -> float:
        '''Returns the recorded temperature of the thermistor, if it is connected to the DISB electronics.
        
        The unit of the returned value depends on the input enum to this function. Options are CELCIUS, FAHRENHEIT or ADC_12BIT.'''
        temperature = ctypes.c_double(0)

        status = ibsen_lib.IBSEN_GetThermistorTemperature(self._m_reg, ctypes.byref(temperature), ctypes.c_int(temp_format))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return temperature.value

    # Permanent memory control ------------------------------------------------------
    def LoadFromPermanentMemory(self):
        '''Loads the settings stored in the permanent memory to all settings of the DISB electronics.'''
        status = ibsen_lib.IBSEN_LoadFromPermanentMemory(self._m_reg, ctypes.byref(self.m_info))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
    def WriteToPermanentMemory(self, prodPass : int):
        '''Writes all the current settings of the DISB electronics to permanent memory on the board. When the DISB electronics are powered on, they read all spectromter settings from this permanent memory.
        
        A password is required to overwrite the permanent memory. Please contact Ibsen Photonics for acquiring the password.'''
        status = ibsen_lib.IBSEN_WriteToPermanentMemory(self._m_reg, ctypes.c_ushort(prodPass))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    # Misc functions ----------------------------------------------------------------
    def UpdateFirmware(self, newFirmware_path : str, programming_password : int):
        r'''Uploads new firmware to the DISB electronics, using a .rpm file. This operation takes between 30-45 seconds and the function will return when the update has finished.
        
        The input parameter newFirmware_path needs the absolute path of the .rpm file, while also containing double backslash as folder separators - For example: "C:Users\\\User\\\Desktop\\\new_firmware.rpd"

        This functions requires a programming password to operate. Please contact Ibsen Photonics for acquiring this password.'''
        status = ibsen_lib.IBSEN_UpdateFirmware(self._m_reg, newFirmware_path.encode('utf-8'), ctypes.c_int(programming_password))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def ResetUSB(self):
        '''Resets the USB connection to the DISB electronics.
        
        This function can be used in case of the operating system corrupting the USB connection during extremely long measurement sessions.'''
        status = ibsen_lib.IBSEN_ResetUSB(ctypes.byref(self._m_reg), ctypes.byref(self._m_stream), ctypes.c_uint(self.m_info.Spectrometer_SerialNumber),
                                          ctypes.byref(self._m_anyDevicesAvailable), ctypes.byref(self._m_single_spectrum_buffer_size),
                                          ctypes.byref(self.m_info))
        
        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def GetFramerate(self) -> float:
        '''Returns the framerate of the spectrometer using the current settings. The framerate unit is Hz.
        
        Decreasing the exposure time and decreasing the region of interest may have a positive effect on the framerate.'''
        framerate = ctypes.c_ushort(0)

        status = ibsen_lib.IBSEN_GetFramerate(ctypes.byref(framerate), self._m_reg, self._m_stream, ctypes.c_double(self.m_timeout_seconds))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return framerate.value

    # TEC Control -------------------------------------------------------------------
    def GetTECsettings(self) -> TEC_Settings:
        '''Gets the status of the setting used to control the TEC of the detector, if the DISB electronics supports it.
        
        This setting controls whether the TEC is enabled and in which type of mode the control of the TEC is running.
        '''
        tec_settings = TEC_Settings()

        status = ibsen_lib.IBSEN_GetTECsettings(self._m_reg, ctypes.byref(tec_settings))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return tec_settings
    
    def SetTECsettings(self, tec_settings : TEC_Settings):
        '''Sets the status of the setting used to control the TEC of the detector, if the DISB electronics supports it.
        
        This setting controls whether the TEC is enabled and in which type of mode the control of the TEC is running.
        '''
        status = ibsen_lib.IBSEN_SetTECsettings(self._m_reg, ctypes.byref(tec_settings))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def GetTECtemperature(self, temp_format : TEMPERATURE_FORMAT) -> float:
        '''Gets the current measured temperature of the TEC module, in the given temperature format.'''
        tec_temp = ctypes.c_double(0)

        status = ibsen_lib.IBSEN_GetTECtemperature(self._m_reg, ctypes.byref(tec_temp), ctypes.c_int(temp_format))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

        return tec_temp.value
    
    def GetPIDtemperatureSetpoint(self, temp_format : TEMPERATURE_FORMAT) -> float:
        '''Gets the current temperature setpoint for the automatic PID control of the TEC module.'''
        pid_temp_setp = ctypes.c_double(0)

        status = ibsen_lib.IBSEN_GetPIDtemperatureSetpoint(self._m_reg, ctypes.byref(pid_temp_setp), ctypes.c_int(temp_format))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

        return pid_temp_setp.value
    
    def SetPIDtemperatureSetpoint(self, pid_temp_setpoint : float, temp_format : TEMPERATURE_FORMAT):
        '''Sets the current temperature setpoint for the automatic PID control of the TEC module.'''
        pid_temp_setpoint_c_type = ctypes.c_double(pid_temp_setpoint)

        status = ibsen_lib.IBSEN_SetPIDtemperatureSetpoint(self._m_reg, pid_temp_setpoint_c_type, ctypes.c_int(temp_format))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def GetPIDcoefficients(self) -> PID_Coefficients:
        '''Gets the current PID coefficients for the automatic PID-based temperature control of the TEC module.'''
        pid_coefs = PID_Coefficients()

        status = ibsen_lib.IBSEN_GetPIDcoefficients(self._m_reg, ctypes.byref(pid_coefs))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

        return pid_coefs

    def SetPIDcoefficients(self, pid_coefs : PID_Coefficients, prodPass : int):
        '''Sets the current PID coefficients for the automatic PID-based temperature control of the TEC module.
        
        This functions requires a production password to operate. Please contact Ibsen Photonics for acquiring this password.
        '''
        status = ibsen_lib.IBSEN_SetPIDcoefficients(self._m_reg, ctypes.byref(pid_coefs), ctypes.c_ushort(prodPass))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])

    def GetFanStatus(self) -> bool:
        '''Get status of external fan control header.'''
        fan_enabled = ctypes.c_bool(False)

        status = ibsen_lib.IBSEN_GetFanStatus(self._m_reg, ctypes.byref(fan_enabled))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return fan_enabled.value
    
    def SetFanStatus(self, fan_enable : bool):
        '''Set status of external fan control header.'''
        status = ibsen_lib.IBSEN_SetFanStatus(self._m_reg, ctypes.c_bool(fan_enable))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetNTCtype(self) -> int:
        '''Get the type of NTC used in the TEC module.
        
        The digit return of this function can be converted to a NTC type using the Register description table(NTC_TYPE) in the hardware manual.
        '''
        ntc_type = ctypes.c_ushort(0)

        status = ibsen_lib.IBSEN_GetNTCtype(self._m_reg, ctypes.byref(ntc_type))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return ntc_type.value
    
    def SetNTCtype(self, ntc_type : int, prodPass : int):
        '''Set the type of NTC used in the TEC module.
        
        The digit return of this function can be converted to a NTC type using the Register description table(NTC_TYPE) in the hardware manual.

        This functions requires a production password to operate. Please contact Ibsen Photonics for acquiring this password.
        '''
        status = ibsen_lib.IBSEN_SetNTCtype(self._m_reg, ctypes.c_ushort(ntc_type), ctypes.c_ushort(prodPass))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
    
    def GetTECstatus(self) -> TEC_Status:
        '''Gets the status of the TEC module.
        
        If any of the error codes descriped in the TEC_Status struct are true, the TEC-module will be turned off until enabled via the SetTECsettings function.
        '''
        tec_status = TEC_Status()

        status = ibsen_lib.IBSEN_GetTECstatus(self._m_reg, ctypes.byref(tec_status))

        # Throw error if not SPECTROMETER_OK
        if status != SPECTROMETER_STATUS.SPECTROMETER_OK:
            raise Exception(error_messages[status])
        
        return tec_status

    def __del__(self):
        if self._m_reg is not None:
            ibsen_lib.IBSEN_closeSpectrometer(self._m_reg, self._m_stream)
