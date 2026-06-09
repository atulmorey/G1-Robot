# Commands — Run these in Ubuntu terminal

## Kill any hanging MoveIt processes
```bash
killall moveit_setup_assistant 2>/dev/null
```

## Create MoveIt config directory
```bash
mkdir -p ~/ros2_ws/src/g1_moveit_config/config
mkdir -p ~/ros2_ws/src/g1_moveit_config/launch
```

## Check G1 URDF joint names (needed for config)
```bash
grep -o 'name="[^"]*"' ~/ros2_ws/src/unitree_ros/robots/g1_description/g1_29dof.urdf | grep -i "shoulder\|elbow\|wrist" | head -20
```
