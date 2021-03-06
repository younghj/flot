#!/usr/bin/env python
import numpy as np
from datetime import datetime
import argparse
import os
import importlib
from env_settings import env_settings
import time
import torch
import rl_util.Roboschool as roboschool
import rl_util.MountainCarContinuousPixel as mountain_env
import time

# Parse the input arguments.
def getInputArgs():
    parser = argparse.ArgumentParser('RL with AI2THOR')
    parser.add_argument('--phase', dest='phase', default='train', type=str, help='train or test')
    parser.add_argument('--algorithm', dest='algorithm', default='A2C', type=str, help='algorithm name')
    args = parser.parse_args()
    return args

def train(agent_class, env_name, seed, training_params, algorithm_params):
    if env_name == "Roboschool":
        env = roboschool.Env()
    else:
        import rl_util.AI2THOREnv as ai2thor
        envs = []
        for i in range(6):
            envs.append(ai2thor.Env())
            time.sleep(3)       

    np.random.seed(seed)
    torch.manual_seed(seed)
    agent = agent_class.Agent(envs, training_params, algorithm_params)
    agent.train()

if __name__ == "__main__":
    args = getInputArgs()
    env_setting = env_settings[args.algorithm]
    
    if args.phase == 'train':
        train(**env_setting)

        # while True:
        #     try:
        #         print("Start!")
        #         train(**env_setting)
        #     except:
        #         pass
        #     else:
        #         break

    else:
        print("ERROR: INVALID ARGUMENT Please choose train or test for phase argument")