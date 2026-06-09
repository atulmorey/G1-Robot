# Commands — Run these in Ubuntu terminal

## Check MoveIt2 installed
```bash
ros2 pkg list | grep moveit
```

## Check G1 URDF exists
```bash
find ~/ros2_ws -name "*.urdf" -o -name "*.xacro" 2>/dev/null | grep -i g1
```
