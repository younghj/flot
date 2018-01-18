import math as m
import numpy as np
from debug import *
import time
from subprocess import Popen
import threading
import traceback
import SigHandler
import atexit

import Pyro4
#
# Initial class to help determine the control API.
class RobotControl(threading.Thread):
    """ Interface to control the actual blimp robot

    RobotControl class communicate with the client's ROS command publishing node
    This class is responsible for the moving the robot, as in taking actions in
    the real environment. Inherits from the Thread class to allow the
    RobotControl to run in the background.

    """

    def __init__(self):
        threading.Thread.__init__(self)
        # self.client = MultirotorClient()
        self.f = 30.
        self.running = False
        self.v_t = 0. # target tangential velocity m/s
        self.v_z = 0. # target velocity in z m/s
        self.w = 0. # target angular velocity m/s
        self.z = None

        # Create Pyro4 object and start up daemon
        self.RC = RobotCommands()
        self.RC.startup()

    def __enter__(self):
        """ Start the thread """
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        """ Exit the thread """
        self.running = False
        self.join()
        return False

    def executeCommand(self):
        """ Send command to publisher """
        """ Use RobotCommands as intermediatary between Python3 and ROS
        Publisher """
        self.RC.setVT(self.v_t)
        self.RC.setVZ(self.v_z)
        self.RC.setW(self.w)
        return


    def setCommand(self, v_t_ref, w_ref, z, v_z_ref=0.):
        """ Set the desired tangential velocity, angular velocity, velocity in z """
        self.v_t = v_t_ref
        self.w = w_ref
        self.v_z = v_z_ref
        self.z = z

    def run(self):
        """ Keep going until obj destruction """
        self.running = True
        while self.running:
            self.executeCommand()

            # Rate limiting
            time.sleep(1/ self.f)
#
# Communication class to send command to Python2 ROS Publisher script
# Ensure that a Pyro4 nameserver is running by calling: pyro4-ns
# pyro4-ns uses the default port 9090 on localhost
# Connect on a seperate python shell with the folllowing lines
""" >>> import Pyro4
    >>> cmd = Pyro4.Proxy("PYRONAME:RobotControl.commands")"""
@Pyro4.expose
class RobotCommands(object):
    ns_process = None
    daemon = None
    ns = None
    uri = None
    dThread = None

    v_t = None
    v_z = None
    w = None

    hasStarted = False

    # Start up daemon server for this object
    def startup(self):
        if not self.hasStarted:
            try:
                # Start up pyro4-ns in a new thread
                self.ns_process = Popen(['pyro4-ns'])

                # Hacky way to wait for start-up; should use STDOUT pipe to confirm
                print('Wait 5 seconds for pyro4-ns to start up...')
                time.sleep(5)

                # Setup and register self
                self.daemon = Pyro4.Daemon()
                self.ns = Pyro4.locateNS()
                self.uri = self.daemon.register(self)
                self.ns.register('RobotControl.commands', self.uri)

                # Create new thread for daemon request loop
                self.dThread = DaemonThread(self.daemon)
                self.dThread.start()

                # Register cleanup on exiting
                atexit.register(self.cleanup)

                self.hasStarted = True
            except:
                print('RobotCommands failed to start!')
                print('Check if another pyro4-ns instance is running, or if '+
                    'another daemon thread is running')
                self.hasStarted = False
        else:
            print('This Pyro4 class has already been started')

    def getVT(self):
        return self.v_t

    def setVT(self, v_t):
        self.v_t = v_t

    def getVZ(self):
        return self.v_z

    def setVz(self, v_z):
        self.v_z = v_z

    def getW(self):
        return self.w

    def setVz(self, w):
        self.w = w

    def cleanup(self):
        if self.ns_process is not None:
            self.ns_process.kill()

        # Need better way to kill this thread properly...
        # if self.dThread is not None:
        #     self.dThread.join()

class DaemonThread(threading.Thread):
    daemon = None

    def __init__(self, daemon):
        threading.Thread.__init__(self)
        self.daemon = daemon

    def run(self):
        self.daemon.requestLoop()