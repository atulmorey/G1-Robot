# Commands — Run these in Ubuntu terminal

## Pull latest
```bash
cd ~/G1-Robot && git pull
```

## Scan point cloud bounds
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/g1_scan_bounds.py
```
