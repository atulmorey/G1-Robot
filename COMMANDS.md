# Commands — Run these in Ubuntu terminal

## Pull and make launcher executable
```bash
cd ~/G1-Robot && git pull
chmod +x ~/G1-Robot/launch_robot_app.sh
```

## Create desktop launcher
```bash
cat > ~/Desktop/RobotControl.desktop << 'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=Robot Control
Comment=Launch G1 Robot Control App
Exec=bash -c "cd ~/G1-Robot && git pull -q && sudo route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1 2>/dev/null && source ~/unitree_ros2/setup.sh && source ~/unitree_ros2/cyclonedds_ws/install/setup.bash && python3 ~/G1-Robot/server.py & sleep 2 && firefox http://localhost:5000"
Icon=utilities-terminal
Terminal=true
DESKTOP
chmod +x ~/Desktop/RobotControl.desktop
```

## Then right-click the desktop icon → "Allow Launching"
