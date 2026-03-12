#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 12 16:08:00 2026

@author: christina strilets

BlackflyCamera class for controlling the FLIR BFS-U3-13Y3M-C USB 3.1 Blackfly
camera via PySpin. Designed to work alongside the DG645 delay generator for 
hardware-triggered image acquisition.
"""

import PySpin
import numpy as np


class BlackflyCamera:
    """
    A class to control a FLIR Blackfly S USB3 camera (BFS-U3-13Y3M-C).
    
    Supports continuous live view and hardware trigger mode (for use with
    the DG645 delay generator). Follows the same class pattern as DelayGen.
    
    Attributes
    ----------
    system : PySpin.System
        The PySpin system instance.
    camera : PySpin.Camera
        The connected PySpin camera object.
    is_connected : bool
        Whether a camera is currently connected and initialized.
    is_acquiring : bool
        Whether the camera is currently acquiring images.
    trigger_mode : str
        Current trigger mode: 'continuous', 'hardware', or 'software'.
    """

    def __init__(self):
        """Initialize the PySpin system. Does not connect to a camera yet."""
        self.system = PySpin.System.GetInstance()
        self.camera = None
        self._is_connected = False
        self._is_acquiring = False
        self.trigger_mode = "continuous"

    # ------------------------------------------------------------------
    #  Connection
    # ------------------------------------------------------------------
    def find_cameras(self):
        """
        Discover all connected FLIR cameras.
        
        Returns
        -------
        list of str
            Serial numbers of all detected cameras.
        """
        cam_list = self.system.GetCameras()
        serials = []
        for i in range(cam_list.GetSize()):
            cam = cam_list.GetByIndex(i)
            serial = cam.TLDevice.DeviceSerialNumber.ToString()
            serials.append(serial)
        cam_list.Clear()
        return serials

    def connect(self, serial_number=None):
        """
        Connect to a camera by serial number, or the first available camera.

        Parameters
        ----------
        serial_number : str, optional
            Serial number of the camera to connect to. If None, connects
            to the first camera found.
        """
        cam_list = self.system.GetCameras()

        if cam_list.GetSize() == 0:
            cam_list.Clear()
            raise RuntimeError("No FLIR cameras detected.")

        if serial_number:
            self.camera = cam_list.GetBySerial(serial_number)
        else:
            self.camera = cam_list.GetByIndex(0)

        cam_list.Clear()

        # Initialize the camera
        self.camera.Init()

        # Configure stream buffer to NewestOnly so we always get the 
        # latest frame and don't fill up the buffer
        s_node_map = self.camera.GetTLStreamNodeMap()
        buffer_handling = PySpin.CEnumerationPtr(
            s_node_map.GetNode("StreamBufferHandlingMode")
        )
        newest_only = buffer_handling.GetEntryByName("NewestOnly")
        buffer_handling.SetIntValue(newest_only.GetValue())

        self._is_connected = True
        info = self.get_camera_info()
        print(f"Connected to camera: {info['name']} (Serial: {info['serial']})")

    # ------------------------------------------------------------------
    #  Camera Info
    # ------------------------------------------------------------------
    def get_camera_info(self):
        """
        Get information about the connected camera.

        Returns
        -------
        dict
            Dictionary with keys 'serial', 'model', 'name'.
        """
        self._check_connected()
        info = {}
        info["serial"] = self.camera.TLDevice.DeviceSerialNumber.ToString()
        info["model"] = self.camera.TLDevice.DeviceModelName.ToString()
        info["name"] = self.camera.TLDevice.DeviceDisplayName.ToString()
        return info

    # ------------------------------------------------------------------
    #  Trigger Configuration
    # ------------------------------------------------------------------
    def configure_continuous(self):
        """
        Configure the camera for continuous acquisition (free-running).
        Disables trigger mode.
        """
        self._check_connected()
        self._ensure_stopped()

        nodemap = self.camera.GetNodeMap()

        # Turn off trigger mode
        trigger_mode_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("TriggerMode")
        )
        trigger_mode_off = trigger_mode_node.GetEntryByName("Off")
        trigger_mode_node.SetIntValue(trigger_mode_off.GetValue())

        # Set acquisition mode to Continuous
        acq_mode_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("AcquisitionMode")
        )
        acq_continuous = acq_mode_node.GetEntryByName("Continuous")
        acq_mode_node.SetIntValue(acq_continuous.GetValue())

        self.trigger_mode = "continuous"
        print("Camera configured for continuous acquisition.")

    def configure_trigger(self, source="hardware"):
        """
        Configure the camera for triggered acquisition.

        Parameters
        ----------
        source : str
            'hardware' for external hardware trigger (Line0 from DG645),
            'software' for software trigger (testing without hardware).
        """
        self._check_connected()
        self._ensure_stopped()

        nodemap = self.camera.GetNodeMap()

        # Set acquisition mode to Continuous (camera stays armed)
        acq_mode_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("AcquisitionMode")
        )
        acq_continuous = acq_mode_node.GetEntryByName("Continuous")
        acq_mode_node.SetIntValue(acq_continuous.GetValue())

        # Turn off trigger mode first to configure it
        trigger_mode_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("TriggerMode")
        )
        trigger_mode_off = trigger_mode_node.GetEntryByName("Off")
        trigger_mode_node.SetIntValue(trigger_mode_off.GetValue())

        # Set trigger selector to FrameStart
        trigger_selector_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("TriggerSelector")
        )
        trigger_selector_fs = trigger_selector_node.GetEntryByName("FrameStart")
        trigger_selector_node.SetIntValue(trigger_selector_fs.GetValue())

        # Set trigger source
        trigger_source_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("TriggerSource")
        )
        if source == "hardware":
            trigger_src_entry = trigger_source_node.GetEntryByName("Line0")
            self.trigger_mode = "hardware"
        elif source == "software":
            trigger_src_entry = trigger_source_node.GetEntryByName("Software")
            self.trigger_mode = "software"
        else:
            raise ValueError(f"Unknown trigger source: {source}")
        trigger_source_node.SetIntValue(trigger_src_entry.GetValue())

        # Set trigger activation to RisingEdge (for hardware trigger)
        if source == "hardware":
            trigger_activation_node = PySpin.CEnumerationPtr(
                nodemap.GetNode("TriggerActivation")
            )
            rising_edge = trigger_activation_node.GetEntryByName("RisingEdge")
            trigger_activation_node.SetIntValue(rising_edge.GetValue())

        # Turn trigger mode back on
        trigger_mode_on = trigger_mode_node.GetEntryByName("On")
        trigger_mode_node.SetIntValue(trigger_mode_on.GetValue())

        print(f"Camera configured for {source} trigger mode.")

    # ------------------------------------------------------------------
    #  Acquisition
    # ------------------------------------------------------------------
    def start_acquisition(self):
        """Start image acquisition."""
        self._check_connected()
        if not self._is_acquiring:
            self.camera.BeginAcquisition()
            self._is_acquiring = True

    def stop_acquisition(self):
        """Stop image acquisition."""
        if self._is_acquiring and self.camera is not None:
            try:
                self.camera.EndAcquisition()
            except PySpin.SpinnakerException:
                pass  # Camera may already have stopped
            self._is_acquiring = False

    def get_image(self, timeout_ms=1000):
        """
        Grab the next available image as a numpy array.

        Parameters
        ----------
        timeout_ms : int
            Timeout in milliseconds to wait for the next image.

        Returns
        -------
        numpy.ndarray or None
            The image data, or None if the image was incomplete.
        """
        self._check_connected()
        try:
            image_result = self.camera.GetNextImage(timeout_ms)
            if image_result.IsIncomplete():
                print("Image incomplete with status: "
                      f"{image_result.GetImageStatus()}")
                image_result.Release()
                return None

            image_data = image_result.GetNDArray().copy()
            image_result.Release()
            return image_data

        except PySpin.SpinnakerException as e:
            # Timeout or other grab error
            print(f"Image grab error: {e}")
            return None

    def capture_triggered_image(self, timeout_ms=5000):
        """
        Wait for a hardware-triggered image and return it.
        
        Use this after the delay generator fires. The camera should already
        be in trigger mode and acquisition should be started.

        Parameters
        ----------
        timeout_ms : int
            How long to wait for the trigger (in milliseconds).

        Returns
        -------
        numpy.ndarray or None
            The captured image, or None on timeout/error.
        """
        self._check_connected()
        return self.get_image(timeout_ms=timeout_ms)

    def software_trigger(self):
        """
        Execute a software trigger. Camera must be in software trigger mode.
        """
        self._check_connected()
        if self.trigger_mode != "software":
            print("Warning: Camera is not in software trigger mode.")
            return

        nodemap = self.camera.GetNodeMap()
        trigger_cmd = PySpin.CCommandPtr(nodemap.GetNode("TriggerSoftware"))
        trigger_cmd.Execute()

    # ------------------------------------------------------------------
    #  Camera Settings
    # ------------------------------------------------------------------
    def set_exposure(self, exposure_us):
        """
        Set the camera exposure time.

        Parameters
        ----------
        exposure_us : float
            Exposure time in microseconds.
        """
        self._check_connected()
        nodemap = self.camera.GetNodeMap()

        # Disable auto exposure
        exposure_auto_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("ExposureAuto")
        )
        exposure_auto_off = exposure_auto_node.GetEntryByName("Off")
        exposure_auto_node.SetIntValue(exposure_auto_off.GetValue())

        # Set exposure time
        exposure_time_node = PySpin.CFloatPtr(
            nodemap.GetNode("ExposureTime")
        )
        # Clamp to valid range
        exposure_us = max(exposure_time_node.GetMin(),
                         min(exposure_us, exposure_time_node.GetMax()))
        exposure_time_node.SetValue(exposure_us)
        print(f"Exposure time set to {exposure_us:.1f} us")

    def set_gain(self, gain_db):
        """
        Set the camera gain.

        Parameters
        ----------
        gain_db : float
            Gain in dB.
        """
        self._check_connected()
        nodemap = self.camera.GetNodeMap()

        # Disable auto gain
        gain_auto_node = PySpin.CEnumerationPtr(
            nodemap.GetNode("GainAuto")
        )
        gain_auto_off = gain_auto_node.GetEntryByName("Off")
        gain_auto_node.SetIntValue(gain_auto_off.GetValue())

        # Set gain
        gain_node = PySpin.CFloatPtr(nodemap.GetNode("Gain"))
        gain_db = max(gain_node.GetMin(),
                      min(gain_db, gain_node.GetMax()))
        gain_node.SetValue(gain_db)
        print(f"Gain set to {gain_db:.2f} dB")

    # ------------------------------------------------------------------
    #  Disconnect / Cleanup
    # ------------------------------------------------------------------
    def disconnect(self):
        """Disconnect the camera and release resources."""
        if self._is_acquiring:
            self.stop_acquisition()

        if self.camera is not None:
            try:
                self.camera.DeInit()
            except PySpin.SpinnakerException:
                pass
            del self.camera
            self.camera = None

        self._is_connected = False
        print("Camera disconnected.")

    def release_system(self):
        """Release the PySpin system instance. Call when fully done."""
        self.disconnect()
        self.system.ReleaseInstance()

    # ------------------------------------------------------------------
    #  Properties
    # ------------------------------------------------------------------
    @property
    def is_connected(self):
        """bool: Whether a camera is connected and initialized."""
        return self._is_connected

    @property
    def is_acquiring(self):
        """bool: Whether the camera is currently acquiring images."""
        return self._is_acquiring

    # ------------------------------------------------------------------
    #  Internal Helpers
    # ------------------------------------------------------------------
    def _check_connected(self):
        """Raise an error if no camera is connected."""
        if not self._is_connected or self.camera is None:
            raise RuntimeError("No camera connected. Call connect() first.")

    def _ensure_stopped(self):
        """Stop acquisition if currently running (required to change settings)."""
        if self._is_acquiring:
            self.stop_acquisition()


# ======================================================================
#  Standalone test
# ======================================================================
if __name__ == "__main__":
    cam = BlackflyCamera()
    
    serials = cam.find_cameras()
    if serials:
        print(f"Found cameras: {serials}")
        cam.connect(serials[0])
        info = cam.get_camera_info()
        print(f"Camera info: {info}")
        cam.disconnect()
    else:
        print("No cameras found.")
    
    cam.release_system()
