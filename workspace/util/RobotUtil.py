# Libraries for video stream client
import sys, time, threading
import numpy as np
from subprocess import Popen, PIPE
from shlex import split
import cv2
from scipy.misc import imsave
import pickle, base64

import torch.multiprocessing as mp
import torch

# Libraries for RobotCameraFeed
import Pyro4
import atexit

# # Image uploading
# import requests
# addr = 'http://localhost:5000/updateImage'
# content_type = 'image/jpeg'
# headers = {'content-type': content_type}

class VideoStreamClient(mp.Process):

    VERBOSE = None
    BGR2RGB = None

    nc_cmd = 'nc -l '
    port = None


    ffmpeg_cmd = [ 'ffmpeg',
            '-framerate', '30',
             '-i', 'pipe:0',           # Use stdin pipe for input
             '-pix_fmt', 'bgr24',      # opencv requires bgr24 pixel format.
             '-vcodec', 'rawvideo',
            '-an','-sn',              # we want to disable audio processing (there is no audio)
            '-f', 'image2pipe', '-']

    # Pipe buffer size calculation for image size
    width = None
    height = None
    depth = None
    num = None
    bufsize = None

    # Pipes, processes, thread
    nc_pipe = None
    pipe = None
    thread = None

    frame = None

    # Class constructor
    def __init__(self, port='2222', width=640, height=480, depth=3, num=2,
                 VERBOSE=False, BGR2RGB=False, saveRoot=None, feedProxy=None):

        super(VideoStreamClient, self).__init__()

        self.port = port
        self.width = width
        self.height = height
        self.depth = depth
        self.num = num
        self.bufsize = width*height*depth*num
        self.ts = 0
        self.VERBOSE = VERBOSE
        self.BGR2RGB = BGR2RGB
        self.saveRoot = saveRoot
        self.frameLock = mp.Lock()
        self.frameNotifier = mp.Event()
        self.sharedFrame = torch.ByteTensor(height, width, depth)
        self.sharedFrame.storage().share_memory_()

        # If RobotCameraFeed Pyro4 proxy has been provided
        if feedProxy is not None:
            self.feed = feedProxy
        else:
            self.feed = None

    def getNCCommand(self):
        return split(self.nc_cmd + self.port)

    # Action when thread is started
    def run(self):
        self.nc_pipe = Popen(self.getNCCommand(), stdout=PIPE)
        self.pipe = Popen(self.ffmpeg_cmd,
                        stdin=self.nc_pipe.stdout,
                        stdout=PIPE,
                        bufsize=self.bufsize)

        if self.VERBOSE:
            print('Listening for video stream...')

        cnt = 0
        while True:
            # Capture frame bytes from pipe
            raw_image = self.pipe.stdout.read(self.width*self.height*self.depth)
            # Transform bytes to numpy array
            image =  np.fromstring(raw_image, dtype='uint8')
            image = image.reshape((self.height, self.width, self.depth))
            if image is not None:
                cnt += 1
                # Convert image from BGR to RGB
                if True:
                    self.frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    self.frame = image

                # Hacky - Saving image at a temp place
                # np.save('/home/kelvin/temp', self.frame)

                # Less hacky way: post to localhost:5000
                # Encode to jpg for faster sending

                # _, img_encoded = cv2.imencode('.jpg', self.frame)
                # requests.post(addr, data=img_encoded.tostring(), headers=headers)


                # Use RobotCameraFeed if its proxy is provided
                # if self.feed is not None:
                #     # Save image to specified path, if provided
                #     savePath = self.feed.getSavePath()
                #     if savePath is not None:
                #         cv2.imwrite(savePath, self.frame)
                #         # Unset save path
                #         self.feed.setSavePath(None)

                #
                # Move the frame into shared memory.
                self.frameLock.acquire()
                self.sharedFrame.copy_(torch.from_numpy(self.frame))
                self.frameLock.release()
                self.frameNotifier.set()
                if self.saveRoot != None:
                    imsave('%s/%s.png'%(self.saveRoot, cnt), self.frame)

                if self.VERBOSE:
                    pass
                    # cv2.imshow('Video', image)
                    cv2.imshow('Video', cv2.cvtColor(self.sharedFrame.numpy(), cv2.COLOR_BGR2RGB))

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            self.pipe.stdout.flush()

        cv2.destroyAllWindows()

    def getFrame(self):
        self.frameNotifier.wait()
        self.frameNotifier.clear()
        self.frameLock.acquire()
        ret = self.sharedFrame.clone().numpy()
        self.frameLock.release()
        return ret

#
# Communication class to expose VideoStreamClient to other processes
# Ensure that a Pyro4 nameserver is running by calling: pyro4-ns
# pyro4-ns uses the default port 9090 on localhost
# Connect on a seperate python shell with the folllowing lines
""" >>> import Pyro4
    >>> cmd = Pyro4.Proxy("PYRONAME:RobotCamera.feed")"""
@Pyro4.expose
class RobotCameraFeed(object):

    # Pyro4 properties
    ns_process = None
    daemon = None
    ns = None
    uri = None
    dThread = None
    proxy = None

    # Class properties
    frame = None    # Frame is stored as encoded string with shape metadata
    savePath = None

    hasStarted = False
    isConnected = False

    # Start up daemon server for this object
    def startup(self, ns_reg = 'RobotCamera.feed'):
        if not self.hasStarted:

            # Find Pyro4 nameserver
            try:
                self.ns = Pyro4.locateNS()
            except:
                # Start up pyro4-ns in a new thread
                self.ns_process = Popen(['pyro4-ns'])

                # Hacky way to wait for start-up; should use STDOUT pipe to confirm
                print('Wait 5 seconds for pyro4-ns to start up...')
                time.sleep(5)

                self.ns = Pyro4.locateNS()

            try:
                # Setup and register self
                self.daemon = Pyro4.Daemon()
                self.uri = self.daemon.register(self)
                self.ns.register(ns_reg, self.uri)

                # Create new thread for daemon request loop
                self.dThread = DaemonThread(self.daemon)
                self.dThread.start()

                # Register cleanup on exiting
                atexit.register(self.cleanup)

                self.hasStarted = True

                print('RobotCameraFeed has started under ' + ns_reg)
            except:
                print('RobotCameraFeed failed to start!')
                print('Check if another pyro4-ns instance is running, or if '+
                    'another daemon thread is running')
                self.hasStarted = False
        else:
            print('This Pyro4 class has already been started')

    # Connect to a nameserver and return the object
    def connect(self, ns_reg = 'RobotCamera.feed'):
        try:
            print('Connecting to nameserver for ' + ns_reg + '...')
            self.proxy = Pyro4.Proxy('PYRONAME:' + ns_reg)
            self.proxy.connected(True)
        except:
            print('Failed to connect to nameserver! Check if it is running.')

    def setFrame(self, frame):
        self.frame = frame

    def getFrame(self):
        return self.frame

    def setSavePath(self, savePath):
        self.savePath = savePath

    def getSavePath(self):
        return self.savePath

    def connected(self, boolean):
        self.isConnected = boolean

    def cleanup(self):
        if self.ns_process is not None:
            self.ns_process.kill()

class DaemonThread(threading.Thread):
    daemon = None

    def __init__(self, daemon):
        threading.Thread.__init__(self)
        self.daemon = daemon

    def run(self):
        self.daemon.requestLoop()
