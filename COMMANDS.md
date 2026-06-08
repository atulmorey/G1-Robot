# Commands — Run these in Ubuntu terminal

## Step 2.1 - Check front camera topic
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 topic info /frontvideostream
```

## Step 2.2 - Check LiDAR topic
```bash
ros2 topic info /utlidar/cloud_livox_mid360
```
