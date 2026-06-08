# Commands — Run these in Ubuntu terminal

## Restart ROS2
```bash
ros2 daemon stop
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 daemon start
ros2 topic list | grep sport
```

## Check sport response topic
```bash
ros2 topic info /api/sport/response
```
