#!/usr/bin/env python
from rospy import Publisher, init_node, Rate, is_shutdown, get_rostime, ROSInterruptException
from std_msgs.msg import Float64
import RPi.GPIO as GPIO
import time
from blimp_control.msg import Float64WithHeader
GPIO.setmode(GPIO.BCM)

TRIG = 23
ECHO = 24

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)

GPIO.output(TRIG, False)
time.sleep(2)

def sonar():
    pub = Publisher('sonar_meas', Float64WithHeader, queue_size=10)
    pub1 = Publisher('sonar_meas_control', Float64, queue_size=10)
    init_node('sonar', anonymous=True)
    rate = Rate(20) # 10hz
    while not is_shutdown():
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        count = 0
        while GPIO.input(ECHO)==0:
            if count>1000:
                break
            pulse_start = time.time()
            count += 1

        count = 0
        while GPIO.input(ECHO)==1:
            if count>1000:
                break
            pulse_end = time.time()
            count += 1

        pulse_duration = pulse_end - pulse_start

        distance = pulse_duration*17150
        distance = distance/100.0

        sonar_data = Float64WithHeader()
        sonar_data.header.stamp = get_rostime()
        if abs(distance) < 2.0:
            sonar_data.float.data = distance
            pub1.publish(distance)
        else:
            sonar_data.float.data = 0.0
            pub1.publish(0.0)
        pub.publish(sonar_data)
        rate.sleep()


if __name__ == '__main__':
    try:
        sonar()
    except ROSInterruptException:
        pass
