# Robot Control App — Commands

## Step 1: Restore and pull latest from GitHub
```bash
cd ~/G1-Robot && git checkout robot_control_app.py && git pull && head -2 ~/G1-Robot/robot_control_app.py
```
If `head -2` shows `#!/usr/bin/env python3` the file is good. If not, run:
```bash
cd ~/G1-Robot && git fetch --all && git reset --hard origin/main && head -2 ~/G1-Robot/robot_control_app.py
```

## Step 2: Test offline (no robot needed)
```bash
python3 ~/G1-Robot/robot_control_app.py --offline
```

## Step 3: Run live (robot must be on + Ethernet connected)
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/robot_control_app.py
```

## Step 4: Create desktop shortcut
```bash
cat > ~/Desktop/RobotControl.desktop << 'EOF'
[Desktop Entry]
Name=Robot Control
Comment=Unitree G1 Executive Demo
Exec=bash -c "source ~/unitree_ros2/setup.sh && source ~/unitree_ros2/cyclonedds_ws/install/setup.bash && python3 ~/G1-Robot/robot_control_app.py"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
EOF
chmod +x ~/Desktop/RobotControl.desktop
```
