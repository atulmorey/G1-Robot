#!/bin/bash
# Robot Control App — Desktop Launcher

cd /home/john/G1-Robot
git pull -q

# Start server
/usr/bin/python3 /home/john/G1-Robot/server.py --offline &

# Wait for server to respond
for i in $(seq 1 15); do
    sleep 1
    if /usr/bin/curl -s http://localhost:5000 > /dev/null 2>&1; then
        break
    fi
    echo "Waiting for server... ($i)"
done

# Open browser
/usr/bin/firefox http://localhost:5000 &

# Keep terminal open
wait
