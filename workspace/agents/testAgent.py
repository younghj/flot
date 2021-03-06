from debug import *
from Actions import Action
import AgentBase as base
import numpy as np
import Observations as obv
import sys

class Agent(base.AgentBase):
    #
    # Initialize.
    def __init__(self, conf):
        super(Agent, self).__init__()
        self.numObs = 17000
        self.obsCount = 0
        self.testAction = None
        print("Running Agent to collect {} Observations".format(self.numObs))
    #
    # Reference to an observation
    def getActionImpl(self):
        if self.obs == None:
            printError("Agent's Observation is None, make sure to giveObservation to Agent before calling getAction")
        else:
            if self.numObs <= self.obsCount:
                print("Data Collection Complete")
                sys.exit()
            self.obsCount += 1
            if self.obsCount % 50 == 0:
                print("{} Data Collected".format(self.obsCount))

            self.testAction = Action( array = abs(np.random.randn(3)*np.array([0,1,0])))
            if self.obs['hasCollided'].val:
                self.testAction = Action(v_t=0.0,w=0.0,isReset=True)

            return self.testAction
