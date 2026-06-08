# Commands — Run these in Ubuntu terminal

## Pull latest
```bash
cd ~/G1-Robot && git pull
```

## Run motion switcher
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/g1_switch_sport.py
```

## Check sport response after running
```bash
ros2 topic info /api/sport/response
```
