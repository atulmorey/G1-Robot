# Commands — Run these in Ubuntu terminal

## Step 1 - Build the unitree_ros package so URDF is findable
```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select unitree_ros --symlink-install 2>&1 | tail -5
```

## Step 2 - Launch MoveIt Setup Assistant
```bash
source ~/ros2_ws/install/setup.bash
ros2 run moveit_setup_assistant moveit_setup_assistant
```
