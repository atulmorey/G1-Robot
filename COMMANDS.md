# Commands — Run these in Ubuntu terminal

## Session startup
```bash
sudo route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
```

## Check LiDAR is live (runs 5 seconds then stops)
```bash
timeout 5 ros2 topic hz /utlidar/cloud_livox_mid360
```
