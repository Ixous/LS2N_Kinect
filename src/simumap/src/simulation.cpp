#include "ros/ros.h"
#include "sensor_msgs/Image.h"
#include "sensor_msgs/LaserScan.h"
#include "nav_msgs/Odometry.h"
#include "tf/tf.h"
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <cv_bridge/cv_bridge.h>
#include <vector>
#include <string>

#define PI 3.14159265359

class Simulation {
private:
    ros::NodeHandle n;
    ros::Publisher pub_img;
    ros::Publisher pub_scan;
    ros::Subscriber sub_odom;
    ros::Rate loop_rate;

    cv_bridge::CvImage img_bridge;
    cv::Mat img_back, img;

    float x, y, theta;

    float RES;
    float ORIGIN_X;
    float ORIGIN_Y;
    float THETA_MAX;
    float THETA_STEP;
    float DIST_MIN;
    float DIST_MAX;
    float DIST_STEP;
    int WALL_BLUE_THRESHOLD;

    void callback(const nav_msgs::Odometry::ConstPtr& msg);
    void simulate();
    void publish();
public:
    Simulation(ros::NodeHandle* _n, int freq);
    ~Simulation();

    void loop();
};

Simulation::Simulation(ros::NodeHandle* _n, int freq) : 
n(*_n) , loop_rate(freq)
{
    sub_odom = n.subscribe("odom", 10, &Simulation::callback, this);
    pub_img = n.advertise<sensor_msgs::Image>("mapimg", 1);
    pub_scan = n.advertise<sensor_msgs::LaserScan>("scan", 1);

    std::string s;
    n.getParam("pgmpath", s);
    img_back = cv::imread(s);
    img = img_back.clone();

    x=0;
    y=0;
    theta=0;

    n.param("/map/resolution", RES, 0.05f);
    n.param("/wall_blue_threshold", WALL_BLUE_THRESHOLD, 50);
    std::vector<double> ORIGIN;
    n.getParam("/map/origin", ORIGIN);
    ORIGIN_X = ORIGIN[0];
    ORIGIN_Y = ORIGIN[1];
    THETA_MAX = PI; // radian
    THETA_STEP = 1.0 * PI/180.0; // radian
    DIST_MIN = 0.12/RES; // pixel
    DIST_MAX = 3.5/RES; // pixel
    DIST_STEP = 1.0; // pixel
}

Simulation::~Simulation()
{
}

void Simulation::loop() {
    while (ros::ok()) {
        ros::spinOnce();
        simulate();
        publish();
        loop_rate.sleep();
    }
}

void Simulation::callback(const nav_msgs::Odometry::ConstPtr& msg) {
    x = msg->pose.pose.position.x;
    y = msg->pose.pose.position.y;
    // theta = msg->pose.pose.orientation.z;
    theta = tf::getYaw(msg->pose.pose.orientation);
}

void Simulation::simulate() {
    // restore the original image to erase the markings
    img = img_back.clone();

    // create the scan message
    sensor_msgs::LaserScan scan_msg;
    scan_msg.header.stamp = ros::Time::now();
    scan_msg.header.frame_id = "base_scan";
    scan_msg.angle_min = 0;
    scan_msg.angle_max = 2*THETA_MAX;
    scan_msg.angle_increment = THETA_STEP;
    scan_msg.range_min = DIST_MIN*RES;
    scan_msg.range_max = DIST_MAX*RES;
    std::vector<float> msg_ranges;
    std::vector<float> msg_intensities;

    // the origin point of the odometry is the center of the map image, converted in pixels with RES
    int x0 = int((x-ORIGIN_X)/RES);
    int y0 = int((y-ORIGIN_Y)/RES);

    // starting values of the raycasting
    float dist = DIST_MIN;
    float phi = theta-THETA_MAX;

    // draw a green square around the position of the robot
    for (int xx = x0-1; xx < x0+2; xx++) {
        for (int yy = y0-1; yy < y0+2; yy++) {
            img.at<cv::Vec3b>(xx,yy) = cv::Vec3b(0,255,0);
        }
    }

    // sweep over the angle
    while (phi<theta+THETA_MAX) {
        bool stop = false;
        // cast ray from DIST_MIN
        while (dist<DIST_MAX && !stop) {
            dist += DIST_STEP;

            // coord of ray point
            int rayx = int(x0+dist*cos(phi));
            int rayy = int(y0+dist*sin(phi));

            // check if outside of the map image
            if (rayx<0 || rayx>img.rows || rayy<0 || rayy>img.cols) {
                dist = 100;
                stop = true;
            } else {
                // TODO : draw sensor data bar
                int a = img.rows-1;
                int b = int((phi-theta+THETA_MAX)*(img.cols-1)/(2*THETA_MAX));
                cv::Vec3b c ((DIST_MAX-dist)*255/DIST_MAX,0,0);
                if (dist>=DIST_MAX-1) c = cv::Vec3b(0,0,0);
                if (b<img.cols && b>0) {
                    for (size_t kkk = 0; kkk < 6; kkk++) {
                        img.at<cv::Vec3b>(a-kkk,b) = c;
                    }
                }

                // check if there is an obstacle using the blue component of the pixel
                if (img_back.at<cv::Vec3b>(rayx,rayy)[2]<=WALL_BLUE_THRESHOLD) {
                    img.at<cv::Vec3b>(rayx,rayy) = cv::Vec3b(255,0,0);
                    stop = true;
                } else {
                    img.at<cv::Vec3b>(rayx,rayy)[1] = 150;

                    // draw orientation of robot
                    if (phi-theta < 0.05 && phi-theta > -0.05)
                            img.at<cv::Vec3b>(rayx,rayy)[0] = 150;
                }
            }
        }
        if (dist>DIST_MAX) dist = 100;
        else dist *= RES;
        msg_ranges.push_back(dist);
        msg_intensities.push_back(0.0);
        dist = DIST_MIN;
        if (phi<theta+THETA_MAX) {
            phi += THETA_STEP;
        }
    }
    scan_msg.ranges = msg_ranges;
    scan_msg.intensities = msg_intensities;
    pub_scan.publish(scan_msg);
}

void Simulation::publish() {
    sensor_msgs::Image img_msg;
    std_msgs::Header header;
    header.stamp = ros::Time::now();
    img_bridge = cv_bridge::CvImage(header, sensor_msgs::image_encodings::RGB8, img);
    img_bridge.toImageMsg(img_msg);
    pub_img.publish(img_msg);
}

int main(int argc, char **argv) {
    ros::init(argc, argv, "simu");
    ros::NodeHandle _n;
    int freq;
    _n.param("simu_freq", freq, 10);
    Simulation simu(&_n, freq);
    simu.loop();
}