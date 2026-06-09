# Commands — Run these in Ubuntu terminal

## Pull latest
```bash
cd ~/G1-Robot && git pull
```

## Verify syntax
```bash
python3 -m py_compile ~/G1-Robot/g1_plan_touch.py && echo "Syntax OK"
```

## Run touch planner (robot must be in standing mode)
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/g1_plan_touch.py
```
