# Commands — Run these in Ubuntu terminal

```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 topic info /lf/sportmodestate --verbose | grep "Topic type" | head -5
```
