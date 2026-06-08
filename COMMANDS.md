# Commands — Run these in Ubuntu terminal

```bash
grep -r "motion_switcher\|api_id\|switch" ~/ros2_ws/src/unitree_ros2/example/src/ --include="*.cpp" --include="*.h" --include="*.hpp" | grep -i "api_id\|motion_switch" | head -20
```
