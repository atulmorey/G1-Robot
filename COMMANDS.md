# Commands — Run these in Ubuntu terminal

## Check sensor message types
```bash
ros2 topic info /frontvideostream
ros2 topic info /utlidar/cloud_livox_mid360
```

## Launch RViz2 to visualize
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 run rviz2 rviz2
```
