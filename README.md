# flot

Autonomous blimp project.

http://meetfibi.com

# Installed Software

- Tensorflow
- PyTorch
- OpenAI Gym
- ROS
- AirSim

Blocks enviroment is included as a packaged version. If full install of AirSim and Unreal Engine/Editor is required, visit:
https://hub.docker.com/r/raejeong/robotics_ws/

# Install

Install docker

Install nvidia-docker

Clone this repo

```cd flot_ws```

Copy the LinuxNoEditor packaged enviroment in the /home/user/workspace/SimulationEnvironments

Edit /opt/ros/kinetic/etc/ros/python_logging.conf on Rpi to remove logging

# Run
```docker build . -t flot_ws ```

```docker stop flot; docker rm flot; nvidia-docker run -it --ipc=host --env="DISPLAY" --env="QT_X11_NO_MITSHM=1" --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" -v $(pwd)/workspace:/home/user/workspace --privileged --net=host --name flot flot_ws```

- to run additional terminal 

```docker exec -it flot bash```

- to kill container

```docker stop flot; docker rm flot```

- useful docker commands

docker system prune --all -f

docker save -o <save image to path> <image name>

docker load -i <path to image tar file>

# Data collection on the rasp pi
1. ```rosmaster --core``` on pi
2. ```roslaunch blimp_control datacollect.launch``` on pi (check if camera_stream.sh script's IP is your ip)
3. Copy data to host from ~/.ros/<date-and-time>
4. ```ffmpeg -i video.h264 image_%06d.png``` to extract training data
5. ```python flot/workspace/tools/blimp_data_postprocessing.py --file <new-file>```
6. ```python flot/workspace/tools/curator/curator.py --path <new-file>```

The data from step 2 will be saved in ~/.ros in a folde

The data here needs to be postprocessed:
Run blimp_data_postprocessing.py --files=<name of folder in .ros e.g. 20180201_0203020>
The out.csv will be outputted to the folder in .ros

Further postprocessing may be required
