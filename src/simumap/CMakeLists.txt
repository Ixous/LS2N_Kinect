cmake_minimum_required(VERSION 2.8.3)
project(simumap)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  genmsg
  std_msgs
  sensor_msgs
  cv_bridge
)

generate_messages(DEPENDENCIES std_msgs)

catkin_package(
  INCLUDE_DIRS
    CATKIN_DEPENDS roscpp
                   sensor_msgs
                   std_msgs
                   cv_bridge
                   image_transport
)

include_directories(
  ${catkin_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
)

add_executable(simumap src/simulation.cpp)
target_link_libraries(simumap ${catkin_LIBRARIES})
add_dependencies(simumap simulation)