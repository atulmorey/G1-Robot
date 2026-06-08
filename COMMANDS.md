# Commands — Run these in Ubuntu terminal

```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
ros2 topic info /api/sport/response --verbose | head -20
```

```bash
ros2 topic echo /api/sport/response --once
```
