import PySpin
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap

class FLIRCameraGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the UI file
        uic.loadUi("flir_camera_gui.ui", self)
        self.setWindowTitle("FLIR Camera GUI")

        # Initialize PySpin camera system
        self.system = PySpin.System.GetInstance()
        self.camera_list = self.system.GetCameras()

        # Populate camera list
        self.populate_camera_list()

        # Connect signals to slots
        self.FindAndConnectButton.clicked.connect(self.find_and_connect_camera)
        self.StartVideoButton.clicked.connect(self.start_video)
        self.StopVideoButton.clicked.connect(self.stop_video)
        self.ModeComboBox.currentIndexChanged.connect(self.change_mode)

        # Create a QTimer for updating video feed
        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.update_video_feed)

        # Initialize video feed variables
        self.video_feed_running = False
        self.camera = None

    def populate_camera_list(self):
        for i in range(self.camera_list.GetSize()):
            camera = self.camera_list.GetByIndex(i)
            self.ModeComboBox.addItem(camera.GetUniqueID())

    def find_and_connect_camera(self):
        # Release previous camera if exists
        if self.camera:
            self.camera.DeInit()
            del self.camera
    
        # Get cameras list again after releasing the previous camera
        cam_list = self.system.GetCameras()
        num_cameras = cam_list.GetSize()
    
        if num_cameras == 0:
            print("No cameras found.")
            return
    
        # Connect to the first camera found
        self.camera = cam_list.GetByIndex(0)
        self.camera.Init()
        print("Camera connected.")


    def start_video(self):
        if self.camera:
            self.camera.BeginAcquisition()
            self.video_feed_running = True
            self.video_timer.start(100)  # Update video feed every 100 ms


    def stop_video(self):
        self.video_feed_running = False
        self.video_timer.stop()

    def change_mode(self):
        if hasattr(self, 'camera'):
            selected_mode = self.ModeComboBox.currentText()
            if selected_mode == "Trigger Mode":
                # Set camera to trigger mode
                self.camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
                print("Trigger mode selected.")
            elif selected_mode == "Continuous Mode":
                # Set camera to continuous mode
                self.camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
                print("Continuous mode selected.")

    def update_video_feed(self):
        if self.camera:
            # Get the latest frame from the camera
            image_result = self.camera.GetNextImage()
            if image_result.IsIncomplete():
                print("Image incomplete")
            else:
                # Get image data
                image_data = image_result.GetNDArray()
    
                # Resize image to fit QLabel dimensions
                label_width = self.VideoFeedLabel.width()
                label_height = self.VideoFeedLabel.height()
                image_data_resized = cv2.resize(image_data, (label_width, label_height))
    
                # Check if the resized image is grayscale or color
                if len(image_data_resized.shape) == 2:
                    # Grayscale image
                    height, width = image_data_resized.shape
                    bytes_per_line = width
                    q_img = QImage(image_data_resized.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
                else:
                    # Color image
                    height, width, channels = image_data_resized.shape
                    bytes_per_line = channels * width
                    q_img = QImage(image_data_resized.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
    
                # Display in QLabel
                self.VideoFeedLabel.setPixmap(QPixmap.fromImage(q_img))
    
                # Release the image
                image_result.Release()



if __name__ == "__main__":
    app = QApplication([])
    gui = FLIRCameraGUI()
    gui.show()
    app.exec_()

