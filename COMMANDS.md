# Commands — Run these in Ubuntu terminal

```bash
grep -r "SelectMode\|select_mode\|normal\|sport\|loco\|ai\|mode" ~/ros2_ws/src/unitree_ros2/example/src/src/g1/ --include="*.cpp" | grep -i "select\|mode_name\|switch" | head -20
```
