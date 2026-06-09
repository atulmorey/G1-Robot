# Commands — Run these in Ubuntu terminal

## Install MoveIt2 for Humble
```bash
sudo apt install -y ros-humble-moveit
```

## Clone Unitree robot descriptions (includes G1 URDF)
```bash
cd ~/ros2_ws/src
git clone https://github.com/unitreerobotics/unitree_ros.git
```

## Check if URDF is now available
```bash
find ~/ros2_ws/src/unitree_ros -name "*.urdf" | grep -i g1
```
