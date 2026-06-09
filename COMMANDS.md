# Commands — Run these in Ubuntu terminal

## Session startup after reboot
```bash
sudo route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 daemon start
```

## Verify robot connected
```bash
ping -c 2 192.168.123.161 && echo "Robot reachable"
```

## Launch MoveIt Setup Assistant
```bash
source ~/ros2_ws/install/setup.bash
ros2 run moveit_setup_assistant moveit_setup_assistant
```
