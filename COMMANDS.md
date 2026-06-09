# Commands — Run these in Ubuntu terminal

## Share output with Claude (replaces copy-paste)
```bash
YOUR_COMMAND > ~/G1-Robot/OUTPUT.md 2>&1 && cd ~/G1-Robot && git add OUTPUT.md && git commit -m "output" && git push
```

## Example — check MoveIt2 installed
```bash
ros2 pkg list | grep moveit > ~/G1-Robot/OUTPUT.md 2>&1 && cd ~/G1-Robot && git add OUTPUT.md && git commit -m "output" && git push
```

## Example — check G1 URDF
```bash
find ~/ros2_ws -name "*.urdf" -o -name "*.xacro" 2>/dev/null | grep -i g1 > ~/G1-Robot/OUTPUT.md 2>&1 && cd ~/G1-Robot && git add OUTPUT.md && git commit -m "output" && git push
```
