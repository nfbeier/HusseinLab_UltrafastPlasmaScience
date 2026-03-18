#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 15:12:00 2026

@author: christina strilets

Standalone FLIR Camera Controller GUI.
Controls a FLIR Blackfly S USB3 camera without a delay generator.
Supports continuous live feed and hardware trigger mode (external trigger).

Requirements:
    - Python 3.10 environment
    - PySpin (Spinnaker Python SDK)
    - numpy < 2  (PySpin was compiled against NumPy 1.x and is incompatible
      with NumPy 2.x. Install with: pip install "numpy<2")
    - pyqtgraph
"""

from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import numpy as np
import os
import cv2
import pyqtgraph as pg

# Makes sure you are in the right path!
cwd = os.getcwd()
if "HusseinLab_UltrafastPlasmaScience" not in cwd.split(os.path.sep):
    raise ValueError("The directory does not contain 'HusseinLab_UltrafastPlasmaScience' folder.")
# Rebuild the directory string up to and including 'HusseinLab_UltrafastPlasmaScience'
cwd = os.path.sep.join(
    cwd.split(os.path.sep)[: cwd.split(os.path.sep).index("HusseinLab_UltrafastPlasmaScience") + 1]
)
os.chdir(cwd)
sys.path.insert(0, cwd)

# Add the FLIR Camera Code directory to path so we can import it
flir_code_dir = os.path.join(
    cwd, "Software", "SolidTargetStage", "Camera Testing", "FLIR Camera Code"
)
sys.path.insert(0, flir_code_dir)
from blackfly_camera import BlackflyCamera

from camera_widget_gui import Ui_Form


#%%
class camera_app(QtWidgets.QWidget):
    def __init__(self):
        super(camera_app, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # =====================================================================
        #  Camera Setup
        # =====================================================================
        self.cam = BlackflyCamera()
        self.cam_connected = False
        self.video_running = False
        self.last_saved_image = None
        self.image_counter = 0

        # Hide ROI and menu buttons on the promoted ImageView widgets
        self.ui.LiveFeedLabel.ui.roiBtn.hide()
        self.ui.LiveFeedLabel.ui.menuBtn.hide()
        self.ui.CapturedImage.ui.roiBtn.hide()
        self.ui.CapturedImage.ui.menuBtn.hide()

        # Set up the video feed timer
        self.video_timer = QtCore.QTimer(self)
        self.video_timer.timeout.connect(self.update_video_feed)

        # Connect camera buttons
        self.ui.FindButton.clicked.connect(self.find_cameras_btn)
        self.ui.ConnectButton.clicked.connect(self.connect_camera)
        self.ui.StartVideoButton.clicked.connect(self.start_video)
        self.ui.StopVideoButton.clicked.connect(self.stop_video)
        self.ui.DisconnectButton.clicked.connect(self.disconnect_camera)
        self.ui.ModeComboBox.currentIndexChanged.connect(self.change_camera_mode)
        self.ui.Cap_Vid_software_Bt.clicked.connect(self.capture_current_image)
        self.ui.save_captured_img.clicked.connect(self.save_captured_image_btn)
        self.ui.Exit_Widget_Button.clicked.connect(self.close)

        # Camera settings inputs
        self.ui.exposure_time_ip.editingFinished.connect(self.apply_exposure_time)
        self.ui.gain_ip.editingFinished.connect(self.apply_gain)

    # ==================================================================
    #  Camera Logging
    # ==================================================================

    def cam_log(self, message):
        """Log a camera message to both the terminal and the GUI display."""
        print(message)
        self.ui.cam_disp_messages.setText(str(message))

    # ==================================================================
    #  Camera Methods
    # ==================================================================

    def find_cameras_btn(self):
        """Find available FLIR cameras and populate the combo box."""
        try:
            serials = self.cam.find_cameras()
            if not serials:
                self.cam_log("No FLIR cameras found.")
                return

            # Populate the combo box with found camera serial numbers
            self.ui.Found_Cam_ComboBox.clear()
            for serial in serials:
                self.ui.Found_Cam_ComboBox.addItem(serial)

            self.cam_log(f"Found {len(serials)} camera(s): {serials}")

        except Exception as e:
            self.cam_log(f"Error finding cameras: {e}")

    def connect_camera(self):
        """Connect to the camera selected in the Found_Cam_ComboBox."""
        selected_serial = self.ui.Found_Cam_ComboBox.currentText()
        if not selected_serial:
            self.cam_log("No camera selected. Click 'Find' first.")
            return

        try:
            # Disconnect existing camera if one is already connected
            if self.cam_connected:
                self.disconnect_camera()

            self.cam.connect(selected_serial)
            self.cam_connected = True

            # Apply the current mode selection
            self.change_camera_mode()

            self.cam_log(f"Camera connected: {selected_serial}")

        except Exception as e:
            self.cam_log(f"Error connecting to camera: {e}")

    def start_video(self):
        """Start the live video feed."""
        if not self.cam_connected:
            self.cam_log("No camera connected.")
            return

        # Make sure we're in continuous mode for live view
        if self.cam.trigger_mode != "continuous":
            self.cam.configure_continuous()
            self.ui.ModeComboBox.setCurrentIndex(0)  # Set combo to "Continuous"

        self.cam.start_acquisition()
        self.video_running = True
        self.video_timer.start(33)  # ~30 fps update rate
        self.cam_log("Live video started.")

    def stop_video(self):
        """Stop the live video feed."""
        self.video_running = False
        self.video_timer.stop()

        if self.cam_connected and self.cam.is_acquiring:
            self.cam.stop_acquisition()

        self.cam_log("Live video stopped.")

    def update_video_feed(self):
        """Timer callback: grab a frame and display it in the live feed."""
        if not self.cam_connected or not self.video_running:
            return

        image = self.cam.get_image(timeout_ms=1000)
        if image is not None:
            self.display_image(image, self.ui.LiveFeedLabel)

    def change_camera_mode(self):
        """Handle camera mode change from the ModeComboBox."""
        if not self.cam_connected:
            return

        # Stop video if running before changing mode
        if self.video_running:
            self.stop_video()

        mode = self.ui.ModeComboBox.currentText().strip()

        if mode == "Continous" or mode == "Continuous":
            self.cam.configure_continuous()
        elif "Hardware Trigger" in mode:
            self.cam.configure_trigger(source="hardware")
            # Start acquisition so camera is armed and waiting for trigger
            self.cam.start_acquisition()
            self.cam_log("Camera armed for hardware trigger. Waiting for external trigger signal.")

    def capture_current_image(self):
        """Capture the current frame from the live feed as a still image."""
        if not self.cam_connected:
            self.cam_log("No camera connected.")
            return

        # If not currently acquiring, start temporarily
        was_acquiring = self.cam.is_acquiring
        if not was_acquiring:
            self.cam.configure_continuous()
            self.cam.start_acquisition()

        image = self.cam.get_image(timeout_ms=2000)
        if image is not None:
            self.last_saved_image = image
            self.image_counter += 1
            self.display_image(image, self.ui.CapturedImage)
            self.cam_log(f"Captured image #{self.image_counter}")
        else:
            self.cam_log("Failed to capture image.")

        # If we started acquisition just for this capture, stop it
        if not was_acquiring:
            self.cam.stop_acquisition()

    def disconnect_camera(self):
        """Disconnect the camera and clean up."""
        if self.video_running:
            self.stop_video()

        if self.cam_connected:
            self.cam.disconnect()
            self.cam_connected = False
            self.cam_log("Camera disconnected.")

    # ==================================================================
    #  Camera Settings
    # ==================================================================

    def apply_exposure_time(self):
        """Read the exposure time input, send to camera, and update with actual value."""
        if not self.cam_connected:
            self.cam_log("No camera connected.")
            return

        text = self.ui.exposure_time_ip.text().strip()
        if not text:
            return

        try:
            requested_us = float(text)
        except ValueError:
            self.cam_log("Invalid exposure time. Enter a number in us.")
            return

        try:
            actual_us = self.cam.set_exposure(requested_us)
            # Update the QLineEdit with the actual value the camera accepted
            self.ui.exposure_time_ip.setText(f"{actual_us:.1f}")
            self.cam_log(f"Exposure set to {actual_us:.1f} us")
        except Exception as e:
            self.cam_log(f"Error setting exposure: {e}")

    def apply_gain(self):
        """Read the gain input, send to camera, and update with actual value."""
        if not self.cam_connected:
            self.cam_log("No camera connected.")
            return

        text = self.ui.gain_ip.text().strip()
        if not text:
            return

        try:
            requested_db = float(text)
        except ValueError:
            self.cam_log("Invalid gain. Enter a number in dB.")
            return

        try:
            actual_db = self.cam.set_gain(requested_db)
            # Update the QLineEdit with the actual value the camera accepted
            self.ui.gain_ip.setText(f"{actual_db:.2f}")
            self.cam_log(f"Gain set to {actual_db:.2f} dB")
        except Exception as e:
            self.cam_log(f"Error setting gain: {e}")

    # ==================================================================
    #  Image Display & Save
    # ==================================================================

    def display_image(self, image_array, image_view):
        """
        Display a numpy image array on a pyqtgraph ImageView widget.

        Parameters
        ----------
        image_array : numpy.ndarray
            The image to display (grayscale or color).
        image_view : pg.ImageView
            The pyqtgraph ImageView widget to display the image on.
        """
        # pyqtgraph expects (width, height) orientation, so transpose
        # autoRange=False after first frame to prevent constant re-scaling
        # autoLevels=False after first frame to keep contrast stable
        image_view.setImage(
            image_array.T,
            autoRange=not self.video_running,
            autoLevels=not self.video_running
        )

    def save_captured_image_btn(self):
        """Save the last captured image as a BMP file."""
        if self.last_saved_image is None:
            self.cam_log("No captured image to save.")
            return

        filename = f"capture_{self.image_counter}.bmp"
        self.save_image(self.last_saved_image, filename)

    def save_image(self, image_array, filepath):
        """
        Save a numpy image array to a file.

        Parameters
        ----------
        image_array : numpy.ndarray
            The image to save.
        filepath : str
            Path to save the image to (e.g., 'capture_001.bmp').
        """
        cv2.imwrite(filepath, image_array)
        self.cam_log(f"Image saved to {filepath}")

    # ==================================================================
    #  Window Close Event
    # ==================================================================
    def closeEvent(self, event):
        """Clean up camera resources when the window is closed."""
        if self.video_running:
            self.stop_video()
        if self.cam_connected:
            self.cam.disconnect()
        self.cam.release_system()
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    application = camera_app()
    application.show()
    sys.exit(app.exec_())
