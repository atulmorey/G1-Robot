# Robot Control App — Commands

## Kill all running instances
```bash
pkill -f robot_control_app.py; pkill -f server.py
```

## Step 1: Pull latest from GitHub
```bash
cd ~/G1-Robot && git checkout robot_control_app.py && git pull
```

## Step 2: Install Flask (one time only)
```bash
pip3 install flask
```

## Step 3: Test offline (no robot needed)
```bash
python3 ~/G1-Robot/server.py --offline
```
Then open http://localhost:5000 in browser.

## Step 4: Run live (robot must be on + Ethernet connected)
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 ~/G1-Robot/server.py
```
Then open http://localhost:5000 in browser.

## Step 5: Create desktop shortcut (opens browser automatically)
```bash
cat > ~/Desktop/RobotControl.desktop << 'EOF'
[Desktop Entry]
Name=Robot Control
Comment=Unitree G1 Web Control
Exec=bash -c "source ~/unitree_ros2/setup.sh && source ~/unitree_ros2/cyclonedds_ws/install/setup.bash && python3 ~/G1-Robot/server.py & sleep 2 && xdg-open http://localhost:5000"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
EOF
chmod +x ~/Desktop/RobotControl.desktop
```

## Access from phone or Windows laptop (same WiFi)
```bash
hostname -I | awk '{print $1}'
```
Use the printed IP: http://THAT_IP:5000
