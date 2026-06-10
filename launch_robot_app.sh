#!/bin/bash
# Robot Control App — Desktop Launcher
# Double-click this file on Ubuntu desktop to start the app

cd ~/G1-Robot
git pull -q

# Fix multicast route (needed after every reboot)
sudo route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1 2>/dev/null

# Source ROS environment
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash

# Start server in background
python3 ~/G1-Robot/server.py &
SERVER_PID=$!

# Wait for server to be ready
sleep 2

# Open browser
xdg-open http://localhost:5000

# Wait for server process (keeps terminal open)
wait $SERVER_PID
