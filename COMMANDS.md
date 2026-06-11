# G1-Robot Discovery Commands

Run this block on the Ubuntu robot laptop before any gesture recording session.

```bash
echo "=== FULL TOPIC LIST WITH TYPES ==="
ros2 topic list -t

echo ""
echo "=== KEY TOPIC FREQUENCIES ==="
echo "/lf/lowstate:"
timeout 3 ros2 topic hz /lf/lowstate 2>&1 | grep -E "average rate|no new" | head -2 || echo "/lf/lowstate: no data"
echo "/lf/sportmodestate:"
timeout 3 ros2 topic hz /lf/sportmodestate 2>&1 | grep -E "average rate|no new" | head -2 || echo "/lf/sportmodestate: no data"
echo "/utlidar/cloud_livox_mid360:"
timeout 3 ros2 topic hz /utlidar/cloud_livox_mid360 2>&1 | grep -E "average rate|no new" | head -2 || echo "/utlidar/cloud_livox_mid360: no data"

echo ""
echo "=== SPORT MODE STATE ==="
timeout 4 ros2 topic echo /lf/sportmodestate --once 2>&1 | head -20 || echo "No sport mode data"

echo ""
echo "=== LOW STATE SAMPLE ==="
timeout 4 ros2 topic echo /lf/lowstate --once 2>&1 | head -50 || echo "No lowstate data"

echo ""
echo "=== RECORDINGS DIRECTORY ==="
ls -lah ~/G1-Robot/recordings/ 2>/dev/null || echo "No recordings yet - directory will be created on first Stop Recording"
```