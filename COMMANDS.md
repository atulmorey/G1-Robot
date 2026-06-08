# Commands — Run these in Ubuntu terminal

## Step 1 - Pull latest
```bash
cd ~/G1-Robot && git pull
```

## Step 2 - Run sport mode switcher
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/g1_switch_sport.py
```

## Step 3 - Check if sport mode is now active
```bash
ros2 topic info /api/sport/response
```
