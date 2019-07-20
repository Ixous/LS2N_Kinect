#!/usr/bin/env python

import rospy
from math import cos, sin
from nav_msgs.msg import Odometry

class Err:
    def __init__(self,freq):
        self.x_gaz = 0
        self.y_gaz = 0
        self.theta_gaz = 0
        self.x_simu = 0
        self.y_simu = 0
        self.theta_simu = 0
        rospy.init_node('calcerr')
        rospy.Subscriber("odom", Odometry, self.receiveGaz)
        rospy.Subscriber("odomsimu", Odometry, self.receiveSimu)
        self.rate = rospy.Rate(freq)

    def loop(self):
        while not rospy.is_shutdown():
            self.log()
            self.rate.sleep()

    def receiveGaz(self,msg):
        self.x_gaz = msg.pose.pose.position.x
        self.y_gaz = msg.pose.pose.position.y
        self.theta_gaz = msg.pose.pose.orientation.z

    def receiveSimu(self,msg):
        self.x_simu = msg.pose.pose.position.x
        self.y_simu = msg.pose.pose.position.y
        self.theta_simu = msg.pose.pose.orientation.z

    def log(self):
        rospy.loginfo("Error : [%f, %f, %f]" % (self.x_gaz-self.x_simu, self.y_gaz-self.y_simu, self.theta_gaz-self.theta_simu))

if __name__ == '__main__':
    errcalctor = Err(100)
    errcalctor.loop()