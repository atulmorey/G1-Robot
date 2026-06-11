# Commands

```bash
echo "=== FULL TOPIC LIST WITH TYPES ==="
ros2 topic list -t

echo ""
echo "=== KEY TOPIC FREQUENCIES ==="
timeout 3 ros2 topic hz /lf/lowstate --once 2>&1 | head -5
timeout 3 ros2 topic hz /lf/sportmodestate --once 2>&1 | head -5
timeout 3 ros2 topic hz /utlidar/cloud_livox_mid360 --once 2>&1 | head -5

echo ""
echo "=== SPORT MODE STATE FIELDS ==="
timeout 3 ros2 topic echo /lf/sportmodestate --once 2>&1 | head -30

echo ""
echo "=== LOW STATE SAMPLE (first 40 lines) ==="
timeout 3 ros2 topic echo /lf/lowstate --once 2>&1 | head -40

echo ""
echo "=== RECORDINGS DIRECTORY ==="
ls -la ~/G1-Robot/recordings/ 2>/dev/null || echo "No recordings yet"
```
