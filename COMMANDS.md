# Commands

```bash
find ~/ros2_ws/src/unitree_ros2/example/src -name "*.cpp" -o -name "*.hpp" -o -name "*.h" | xargs grep -l "arm_task\|ArmTask\|ARM_TASK" 2>/dev/null
```
