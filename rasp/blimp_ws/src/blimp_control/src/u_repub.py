#!/usr/bin/env python
import rospy
from std_msgs.msg import Float64

u = 0
pub0 = rospy.Publisher('prop_down_re', Float64, queue_size=1)
pub1 = rospy.Publisher('delta_re', Float64, queue_size=1)
count = 0

thresh = 1

def callback0(data):
    global count
    u = data.data
    count += 1
    if count > 1:
        pub0.publish(u)
        count = 0

def callback1(data):
    global count
    u = data.data
    count += 1
    if count > thresh:
        pub1.publish(u)
        count = 0

def u_repub():
    # In ROS, nodes are uniquely named. If two nodes with the same
    # node are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
    rospy.init_node('u_repub', anonymous=True)
    rospy.Subscriber("prop_down", Float64, callback0)
    rospy.Subscriber("delta", Float64, callback1)
    rospy.spin()



if __name__ == '__main__':
    u_repub()
