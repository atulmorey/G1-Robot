# Commands — Run these in Ubuntu terminal

## Pull latest
```bash
cd ~/G1-Robot && git pull
```

## Run the app
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/robot_control_app.py
```

## Run offline (no robot needed)
```bash
python3 ~/G1-Robot/robot_control_app.py --offline
```
