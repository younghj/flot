#!/usr/bin/env python
import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def getInputArgs():
    parser = argparse.ArgumentParser('Postprocessing for blimp')
    parser.add_argument('--path', dest='dataPath', default=None, type=str, help='Path to the data to score.')
    parser.add_argument('--thresh', dest='thresh', default=0.02,  type=float, help='Acceleration threshold.')
    parser.add_argument('--shmidt', dest='shmidt', default=1., type=float, help='Minimum time (sec) before considering the next value a seperate collision.')
    args = parser.parse_args()
    return args

def main(d):
    #
    # Load data.
    outname = 'out.csv'
    path = os.path.abspath(args.dataPath)
    df = pd.read_csv(path + '/imu-observation.csv')
    df = df.rename(columns=lambda x: x.strip())
    #
    # Get time differences.
    tDiffs = np.diff(df['Timestamp'])
    tAvg = np.mean(tDiffs)
    frameHold = args.shmidt // tAvg
    #
    # Get ACC norm.
    a_x = df['LinAcc(x)']
    a_y = df['LinAcc(y)']
    a_z = df['LinAcc(z)']
    a_x2 = df['LinAcc(x)'] ** 2
    a_y2 = df['LinAcc(y)'] ** 2
    a_z2 = df['LinAcc(z)'] ** 2
    norm = np.sqrt(a_x2 + a_y2 + a_z2)
    norm_xy = np.sqrt(a_x2 + a_y2)
    #
    # Gather statistics.
    baseline = np.mean(norm)
    norm -= baseline
    thresh = args.thresh
    col_idx = np.squeeze(np.argwhere(norm > thresh))
    sp = np.split(norm, col_idx)
    # #
    # # Drop first list since it does not have a value above the treshold at the beginning.
    # sp = sp[1:]
    #
    # Filter by length of each split.
    cnt = 0
    colMax = []
    sects = [sp[0]]
    for sectIdx in range(len(sp) - 1):
        nxt = sectIdx + 1
        sect = sp[nxt]
        if len(sect) > frameHold:
            cnt += 1
            sectSummary = np.concatenate(sects)
            colMax.append(np.max(sectSummary))
        else:
            sects.append(sect)
    print(cnt)
    print(colMax)
    print(baseline)
    # plt.figure()
    # plt.plot(norm_xy)
    # plt.figure()
    # plt.plot(norm)
    # plt.show()

if __name__=='__main__':
    args = getInputArgs()
    main(args)
