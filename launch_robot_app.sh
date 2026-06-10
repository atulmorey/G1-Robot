#!/bin/bash
# Robot Control App — Desktop Launcher

cd /home/john/G1-Robot
git fetch origin -q && git reset --hard origin/main -q

# Kill any existing server on port 5000
pkill -9 -f "server.py" 2>/dev/null
fuser -k 5000/tcp 2>/dev/null
sleep 4

# Log output for debugging
LOG=/home/john/robot_app.log
echo "=== Starting $(date) ===" > $LOG

# Fix multicast route (silently, in case Ethernet not connected yet)
route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1 2>/dev/null || true

# Source ROS environment
source /home/john/unitree_ros2/setup.sh >> $LOG 2>&1
source /home/john/unitree_ros2/cyclonedds_ws/install/setup.bash >> $LOG 2>&1

# Export so subprocesses inherit
export ROS_DISTRO=humble
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/john/cyclone_g1.xml
export AMENT_PREFIX_PATH
export LD_LIBRARY_PATH
export PYTHONPATH

# Start server and capture output
/usr/bin/python3 /home/john/G1-Robot/server.py >> $LOG 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID" >> $LOG

# Wait for server to respond (up to 15 seconds)
for i in $(seq 1 15); do
    sleep 1
    echo "Waiting... $i" >> $LOG
    if /usr/bin/curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "Server ready!" >> $LOG
        break
    fi
    echo "Waiting for server... ($i)"
    # Check if server crashed
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "SERVER CRASHED - check $LOG"
        cat $LOG
        read -p "Press Enter to close..."
        exit 1
    fi
done

# Open browser
/usr/bin/firefox http://localhost:5000 &

# Keep terminal open
wait
