# Commands — Run these in Ubuntu terminal

## Check arm API topic type
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 topic info /api/arm/request --verbose | head -15
```

## Check arm action state
```bash
ros2 topic echo /arm/action/state --once
```

## Find arm API examples
```bash
grep -r "api/arm\|arm_sdk\|ArmSDK" ~/ros2_ws/src/unitree_ros2/example/src/ --include="*.cpp" --include="*.hpp" | head -15
```
