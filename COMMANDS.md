# Commands — Run these in Ubuntu terminal

## Fix multicast route (must do after every reboot)
```bash
sudo route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1
```

## Restart ROS and check connection
```bash
ros2 daemon stop
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 daemon start
ping -c 2 192.168.123.161 && echo "Robot reachable" || echo "Robot NOT reachable"
```

## Check topics
```bash
ros2 topic list > /tmp/topics.txt && wc -l /tmp/topics.txt && grep -E "video|lidar|utlidar" /tmp/topics.txt
```
