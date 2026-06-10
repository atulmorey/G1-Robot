#!/bin/bash
# Robot Control App — Desktop Launcher

cd /home/john/G1-Robot
git pull -q

# Log output for debugging
LOG=/home/john/robot_app.log
echo "=== Starting $(date) ===" > $LOG

# Start server and capture output
/usr/bin/python3 /home/john/G1-Robot/server.py --offline >> $LOG 2>&1 &
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
