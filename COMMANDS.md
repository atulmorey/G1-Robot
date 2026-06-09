# Commands — Run these in Ubuntu terminal

## Get right arm joint names too
```bash
grep -o 'name="[^"]*"' ~/ros2_ws/src/unitree_ros/robots/g1_description/g1_29dof.urdf | grep -i "right.*shoulder\|right.*elbow\|right.*wrist" | grep "joint" | head -10
```
