# Commands — Run these in Ubuntu terminal (robot standing)

## Check if /armsdk has any subscribers
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 topic info /armsdk
```

## Check /arm_sdk topic
```bash
ros2 topic info /arm_sdk
```

## Check all arm-related topics
```bash
ros2 topic list | grep -i arm
```
