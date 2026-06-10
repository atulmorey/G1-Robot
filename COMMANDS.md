# Commands — Run these in Ubuntu terminal

## Find head joint names in URDF
```bash
grep -o 'name="[^"]*"' ~/ros2_ws/src/unitree_ros/robots/g1_description/g1_29dof.urdf | grep -i "head\|neck" | head -10
```

## Check arm API topic
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 topic info /api/arm/request --verbose | head -20
```
