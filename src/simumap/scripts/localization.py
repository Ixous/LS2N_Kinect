#!/usr/bin/env python
import rospy
from math import cos, sin
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf2_msgs.msg import TFMessage
from tf.transformations import quaternion_from_euler
from geometry_msgs.msg import TransformStamped


class Localization:
    # constructor
    def __init__(self, freq=100, x0=0, y0=0, theta0=0):
        self.freq = freq
        self.dt = 1.0/freq # seconds
        self.x = x0 # meters
        self.y = y0 # meters
        self.theta = theta0 # rad
        self.cmd_v = 0 # meters/sec
        self.cmd_omega = 0 # rad/sec

        rospy.init_node('loc')
        rospy.Subscriber("cmd_vel", Twist, self.callback)
        self.pub_odom = rospy.Publisher('odom', Odometry, queue_size=5)
        self.pub_tf = rospy.Publisher('tf_static', TFMessage, queue_size=5)
        self.rate = rospy.Rate(self.freq)


    def loop(self):
        while not rospy.is_shutdown():
            self.update()
            self.publishOdom()
            self.log()
            self.rate.sleep()

    def callback(self,msg):
        self.cmd_v = msg.linear.x
        self.cmd_omega = msg.angular.z

    def update(self):
        self.x += self.cmd_v * cos(self.theta) * self.dt
        self.y += self.cmd_v * sin(self.theta) * self.dt
        self.theta += self.cmd_omega * self.dt

    def publishOdom(self):
        odom = Odometry()
        odom.header.stamp = rospy.Time.now()
        odom.header.frame_id = "base_link";
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        # odom.pose.pose.orientation.z = self.theta
        odom.pose.pose.orientation.x = quaternion_from_euler(0,0,self.theta)[0]
        odom.pose.pose.orientation.y = quaternion_from_euler(0,0,self.theta)[1]
        odom.pose.pose.orientation.z = quaternion_from_euler(0,0,self.theta)[2]
        odom.pose.pose.orientation.w = quaternion_from_euler(0,0,self.theta)[3]
        odom.twist.twist.linear.x = self.cmd_v
        odom.twist.twist.angular.z = self.cmd_omega
        self.pub_odom.publish(odom)
        # rospy.logwarn("Publish : [%f, %f, %f]" % (odom.pose.pose.position.x, odom.pose.pose.position.y, odom.pose.pose.orientation.z))

    def log(self):
        rospy.loginfo("Odom : [%f, %f, %f]" % (self.x, self.y, self.theta))

if __name__ == '__main__':
    loc = Localization(rospy.get_param('/odom_freq'), rospy.get_param('/x_init'), rospy.get_param('/y_init'), rospy.get_param('/theta_init'))
    loc.loop()
