# Commands — Run these in Ubuntu terminal

## Session startup
```bash
ros2 daemon stop
sudo route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 daemon start
```

## Confirm robot connected and sensors visible
```bash
ping -c 2 192.168.123.161 && ros2 topic list | grep -E "video|lidar|utlidar|camera"
```
