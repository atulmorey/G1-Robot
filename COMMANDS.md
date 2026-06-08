# Commands — Run these in Ubuntu terminal

## Proper G1 Stand Sequence using Loco Client

### Step 1 — Source environment
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
```

### Step 2 — Damp (safe limp mode)
```bash
~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_loco_client_example --damp
```

### Step 3 — Start locomotion controller
```bash
~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_loco_client_example --start
```

### Step 4 — Stand up with balance
```bash
~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_loco_client_example --stand_up
```

### Optional — Balance stand (more stable)
```bash
~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_loco_client_example --balance_stand
```
