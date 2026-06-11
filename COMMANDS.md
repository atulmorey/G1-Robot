# Commands

```bash
echo "=== 1. SPORT MODE STATE (force unitree_hg type) ==="
timeout 5 ros2 topic echo /lf/sportmodestate unitree_hg/msg/SportModeState --once 2>&1 | head -20 || echo "No sport mode data with hg type"

echo ""
echo "=== 2. SPORT MODE STATE (try unitree_go type) ==="
timeout 5 ros2 topic echo /lf/sportmodestate unitree_go/msg/SportModeState --once 2>&1 | head -20 || echo "No sport mode data with go type"

echo ""
echo "=== 3. GESTURE RESULT TOPIC (listen 5s — trigger a gesture NOW) ==="
timeout 5 ros2 topic echo /gesture/result 2>&1 || echo "No gesture result in 5s"

echo ""
echo "=== 4. ARM ACTION STATE ==="
timeout 3 ros2 topic echo /arm/action/state --once 2>&1 | head -10 || echo "No arm action state"

echo ""
echo "=== 5. CONTROLLER INPUT ==="
timeout 3 ros2 topic echo /wirelesscontroller --once 2>&1 | head -20 || echo "No controller data"

echo ""
echo "=== 6. ODOMETRY ==="
timeout 3 ros2 topic echo /dog_odom --once 2>&1 | head -20 || echo "No odom data"

echo ""
echo "=== 7. HAND STATE ==="
timeout 3 ros2 topic echo /lf/dex3/right/state --once 2>&1 | head -20 || echo "No hand state"

echo ""
echo "=== 8. BATTERY STATE ==="
timeout 3 ros2 topic echo /lf/bmsstate --once 2>&1 | head -15 || echo "No BMS state"

echo ""
echo "=== 9. LOWSTATE FREQUENCY (3s sample) ==="
timeout 3 ros2 topic hz /lf/lowstate 2>&1 | grep -E "average rate|min|max" | head -3

echo ""
echo "=== Done ==="
```
