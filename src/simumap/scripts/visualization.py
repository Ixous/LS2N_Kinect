#!/usr/bin/env python
import rospy
import cv2
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image

class Visualization:
    def __init__(self):
        rospy.init_node('visalization')
        rospy.Subscriber("mapimg",Image,self.callback)
        self.bridge = CvBridge()
    
    def callback(self,msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            print e
        cv2.namedWindow('Image window', cv2.WINDOW_NORMAL)
        if rospy.get_param('/resizeWindow'):
            height, width, channels = cv_image.shape
            ratio = height/width
            windowWidth = rospy.get_param('/windowWidth')
            cv_imageS = cv2.resize(cv_image, (windowWidth, ratio*windowWidth))
            cv2.imshow("Image window", cv_imageS)
        else:
            cv2.imshow("Image window", cv_image)
        cv2.waitKey(3)

if __name__ == '__main__':
    visu = Visualization()
    rospy.spin()
    cv2.destroyAllWindows()

