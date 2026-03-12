import os

import matplotlib.pyplot as plt
import numpy as np
import time
from SimpleFLIR import Camera, GetBFSCameras


class CameraNotConnected(Exception):
    pass


class ListCameras:
    def __init__(self):
        self.camlist = GetBFSCameras().getCameras()

    def get(self):
        return self.camlist


class RunBlackFlyCamera:
    # Todo: loop upon instantiation to get commands from queue (as input when creating)
    #       Handle the inputs for shutdown
    #       Handle how to implement hardware trigger
    #       Move this to new file bc it'll get specialized quick
    """
    Per-camera instance of this is required. Deals with a hardware trigger (currently software as no hardware triggers
    have been configured) and writes data to specified file directory so that the file daemon can transfer it to the
    queue for writing to shot hdf5 file
    """

    def __init__(self, camserial, filenum):
        """
        Initalizes camera from input serial number and starting filename

        :param camserial: Camera's serial number
        :param filenum: number to start numbering files at
        """
        try:
            self.cam = Camera(camserial)
        except:
            raise CameraNotConnected('Camera ' + camserial + ' not connected.')

        self.camserial = camserial
        self.camName = self.cam.getDeviceName()
        self.filenum = filenum
        self.datafilename = self.camserial + '_shotdata_' + '0' * (4 - len(str(self.filenum))) + str(filenum) + '.npy'
        # self.metadatafilename = self.camserial + '_shotmetadata_' + '0' * (4 - len(str(self.filenum))) + str(
        #     filenum) + '.npy'

        # set file directory
        self.filepath = 'TempDataFiles/' + self.camserial + '/'

        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)

        # initialize camera
        self.cam.init()

        # todo: run trigger watch loop here?

    def adjust(self, target, value):
        self.cam.setattr(target, value)

    def get(self, attr):
        return self.cam.getDeviceParams(attr)

    def wait_for_trigger(self):
        pass

    def handleTrigger(self):
        self.filenum += 1
        self.__saveData(self.cam.get_array())

    def get_image_array(self):
        return self.cam.get_array()

    def __getShotMetadata(self):
        return self.cam.getDeviceParams()

    def __saveData(self, data):
        self.datafilename = self.camserial + '_shotdata_' + '0' * (4 - len(str(self.filenum))) + str(
            self.filenum) + '.npy'
        returndict = {}
        returndict['diagnosticname'] = self.camName + ' Serial: ' + self.camserial
        returndict['targetfile'] = self.filenum
        returndict['data'] = data
        returndict['metadata'] = self.__getShotMetadata()
        np.save(self.filepath + self.datafilename, returndict)
        print('Saved image ' + self.datafilename)

    def start(self):
        self.cam.start()

    def stop(self):
        self.cam.stop()

    def close(self):
        self.cam.close()

    def printInfo(self):
        self.cam.document()

    def liveView(self):
        self.isLiveOut = True
        self.cam.configliveout()
        self.cam.start()
        fig = plt.figure(1)
        fig.canvas.mpl_connect('close_event', self.__closeLiveView)

        while self.isLiveOut:
            image = self.cam.get_array()
            plt.imshow(image, cmap='Spectral')
            plt.colorbar()
            plt.pause(0.001)
            plt.clf()

    def __closeLiveView(self, event):
        self.isLiveOut = False


if __name__ == '__main__':
    camera = RunBlackFlyCamera('19129388', 1)
    #camera.start()
    #camera.stop()
    camera.close()
