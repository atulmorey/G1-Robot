# Commands — Run these in Ubuntu terminal

## Check if MoveIt2 is installed
```bash
ros2 pkg list | grep moveit
```

## Check if G1 URDF exists
```bash
find ~/ros2_ws -name "*.urdf" -o -name "*.xacro" | grep -i g1 | head -10
```

## Check if unitree description package exists
```bash
find / -name "*.urdf" 2>/dev/null | grep -i "g1\|unitree" | head -10
```
