#!/usr/bin/env bash

foldername=$(date +%Y%m%d-%H%M%S)
echo $foldername
mkdir $foldername
cd $foldername

airsim_log=airsim_$foldername.log
python_log=python_agent_$foldername.log

while :
do

    echo "run $COUNT"
    echo -e "\nrun $COUNT\n" >> $airsim_log
    echo -e "\nrun $COUNT\n" >> $python_log
########################################## CHANGE THIS DIRECTORY. NOTE: that it isn't the OrangeRoom.sh, you have to go 2 more folders down to just "OrangeRoom"
#~/Downloads/LinuxNoEditor/OrangeRoom/Binaries/Linux/OrangeRoom OrangeRoom -windowed >> $airsim_log 2>&1 &
    /home/ddworakowski/flot/workspace/testEnvs/berlin/xoioBerlinFlat/Binaries/Linux/xoioBerlinFlat xoioBerlinFlot -windowed >> $airsim_log 2>&1 &
    AIRSIM_PID=$!
    sleep 10s

########################################## CHANGE THIS DIRECTORY
    timeout -sHUP 10m python3 ~/flot/workspace/runAgent.py --agent=dataCollectionAgent --config=dataCollectionAgentConfig >> $python_log 2>&1
    ps aux | grep -i runAgent

    echo -e "CRASHED\n\n"
    kill -9 $AIRSIM_PID
    sleep 7s
    COUNT=$(( $COUNT + 1  ))

done

