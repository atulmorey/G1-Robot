# Commands — Run these in Ubuntu terminal

## Pull latest
```bash
cd ~/G1-Robot && git pull
```

## Run mode switcher (robot must be in green/dev mode)
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/g1_switch_sport.py
```

## Check sport response after
```bash
ros2 topic info /api/sport/response
```
