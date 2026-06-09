# Commands — Next Session Priority

## 1. Session startup
```bash
sudo route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
```

## 2. Robot startup sequence
# Power on → purple light
# L2 + R2 → green (dev mode)
# L2 + B → damping
# L2 + A → stand (robot stands freely without harness!)

## 3. Check /api/arm/request topic type
```bash
ros2 topic info /api/arm/request --verbose | head -15
```

## 4. Check arm action state
```bash
ros2 topic echo /arm/action/state --once
```

## 5. Find arm API examples in source
```bash
grep -r "api/arm\|arm_sdk\|ArmSDK" ~/ros2_ws/src/unitree_ros2/example/src/ --include="*.cpp" --include="*.hpp" | head -15
```

## 6. Run touch planner after fixing arm API
```bash
python3 ~/G1-Robot/g1_plan_touch.py
```
