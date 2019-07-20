#!/usr/bin/env python
import rospy
import cv2
from cv_bridge import CvBridge, CvBridgeError
from math import cos, sin, pi
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image
from copy import copy

# should be moved inside the class
RES = rospy.get_param('/map/resolution') # meter/pixel
ORIGIN_X = rospy.get_param('/map/origin')[1]
ORIGIN_Y = rospy.get_param('/map/origin')[0]
THETA_MAX = pi # radian
THETA_STEP = 1 * pi/180 # radian
DIST_MIN = 0.12/RES # pixel
DIST_MAX = 3.5/RES # pixel
DIST_STEP = 1 # pixel

class Simulation:
    # constructor
    def __init__(self, freq=5):
        # position and orientation of the robot
        self.x = 0 # meter
        self.y = 0 # meter
        self.theta = 0 # radian

        # ROS
        rospy.init_node('simu')
        rospy.Subscriber("odom", Odometry, self.callback)
        self.pub = rospy.Publisher('mapimg', Image, queue_size=1)

        # refresh rate
        self.freq = freq # Hz useless should be deleted
        self.rate = rospy.Rate(self.freq)

        # OpenCV
        self.bridge = CvBridge()
        self.img_original = cv2.imread("/home/louis/ros/src/MOBRO_ROS/maps/house.pgm")
        self.img = copy(self.img_original)



    def loop(self):
        while not rospy.is_shutdown():
            self.simulate()
            self.publish()
            self.rate.sleep()



    def callback(self,msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.theta = msg.pose.pose.orientation.z



    def publish(self):
        try:
            self.pub.publish(self.bridge.cv2_to_imgmsg(self.img, "bgr8"))
        except CvBridgeError as e:
            print e



    def simulate(self):
        # restore the original image to erase the markings
        self.img = copy(self.img_original)

        # the origin point of the odometry is the center of the map image, converted in pixels with RES
        x0 = int((self.x-ORIGIN_X)/RES)
        y0 = int((self.y-ORIGIN_Y)/RES)
        # x0 = int(self.img.shape[1]/2 + self.x/RES)
        # y0 = int(self.img.shape[0]/2 + self.y/RES)
        # rospy.logerr("should be %d    but is %d" % (self.img.shape[1]/2,-ORIGIN_X/RES))
        # rospy.logerr("should be %d    but is %d" % (self.img.shape[0]/2,-ORIGIN_Y/RES))
        
        # x0 = int((ORIGIN_X+self.x)/RES) NE MARCHE PAS !! POURQUOI ?
        # y0 = int(ORIGIN_Y/RES + self.y/RES)

        # stqrting values of the raycasting
        dist = DIST_MIN
        theta = self.theta-THETA_MAX

        # draw a green square around the position of the robot
        for xx in range(x0-1,x0+2):
            for yy in range(y0-1,y0+2):
                self.img[yy,xx] = [0,255,0]
        
        # sweep over the angle
        while theta < self.theta+THETA_MAX:
            # cast ray from DIST_MIN
            while dist < DIST_MAX:
                dist+=DIST_STEP
                x = int(x0+dist*cos(theta))
                y = int(y0+dist*sin(theta))
                # check if outside of the map image
                if x not in range(0,self.img.shape[1]) or y not in range(0,self.img.shape[1]):
                    dist = DIST_MAX
                else:
                    # draw sensor data bar
                    a = self.img.shape[0]-1
                    b = int((theta-self.theta+THETA_MAX)*(self.img.shape[1]-1)/(2*THETA_MAX))
                    c = [0,0,(DIST_MAX-dist)*255/DIST_MAX]
                    if dist>=DIST_MAX-1: c = [0,0,0]
                    if b<self.img.shape[1] and b>0:
                        self.img[a , b] = c
                        self.img[a-1 , b] = c
                        self.img[a-2 , b] = c
                        self.img[a-3 , b] = c
                        self.img[a-4 , b] = c
                        self.img[a-5 , b] = c
                    
                    # check if there is an obstacle using the blue componemt of the pixel
                    if self.img[y,x,0]==0:
                        self.img[y,x] = [0,0,255]
                        dist = DIST_MAX # to exit the while loop
                    else:
                        self.img[y,x,1] = 150

                        # draw orientation of robot
                        if theta-self.theta < 0.05 and theta-self.theta > -0.05:
                            self.img[y,x,2] = 150
                    

                    
            dist = DIST_MIN
            if theta < self.theta+THETA_MAX:
                theta += THETA_STEP



if __name__ == '__main__':
    simu = Simulation(5)
    simu.loop()
