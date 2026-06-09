# Robot Control App — Commands

## Step 1: Download the app to Ubuntu
```bash
curl -o ~/G1-Robot/robot_control_app.py https://raw.githubusercontent.com/atulmorey/G1-Robot/main/robot_control_app.py
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
