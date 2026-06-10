# Commands — Run these in Ubuntu terminal

## Pull latest (gets new capability buttons)
```bash
cd ~/G1-Robot && git pull
```

## Restart web app to pick up new capabilities
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/server.py
```

## Then open browser at:
# http://localhost:5000
# You should see two updated buttons: "Detect Objects" and "Touch Object"
