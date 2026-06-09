# Commands — Run these in Ubuntu terminal

## Check current FSM ID (robot must be on)
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
timeout 5 ~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_loco_client_example --get_fsm_id
```
