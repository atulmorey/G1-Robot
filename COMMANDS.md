# Commands

```bash
echo "=== 1. ROS Topics Available ==="
ros2 topic list | grep -E "lowstate|sportmode|armsdk|utlidar|cloud" || echo "No matching topics - ROS not running?"

echo ""
echo "=== 2. Robot Connection + Mode ==="
timeout 4 ros2 topic echo /lf/lowstate --once 2>&1 | grep -E "mode_machine|connected" | head -5 || echo "No /lf/lowstate - robot not connected"

echo ""
echo "=== 3. Sport Mode State ==="
timeout 4 ros2 topic echo /lf/sportmodestate --once 2>&1 | grep -E "mode:|gait" | head -5 || echo "No /lf/sportmodestate"

echo ""
echo "=== 4. Current Arm Joint Positions ==="
python3 - <<'PYEOF'
import sys
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy
    from unitree_hg.msg import LowState

    rclpy.init()
    class QuickCheck(Node):
        def __init__(self):
            super().__init__('quick_check')
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.msg = None
            self.create_subscription(LowState, '/lf/lowstate', lambda m: setattr(self, 'msg', m), qos)

    n = QuickCheck()
    for _ in range(60):
        rclpy.spin_once(n, timeout_sec=0.1)
        if n.msg:
            break

    if n.msg:
        joints = n.msg.motor_state
        print("Right arm joints:")
        labels = {22: "R_shoulder_pitch", 23: "R_shoulder_roll", 24: "R_shoulder_yaw", 25: "R_elbow", 26: "R_wrist_roll"}
        for i in [22, 23, 24, 25, 26]:
            print(f"  [{i}] {labels[i]}: q={joints[i].q:.3f} rad  tau={joints[i].tau:.3f} Nm")
        print(f"IMU: roll={n.msg.imu_state.rpy[0]:.3f}  pitch={n.msg.imu_state.rpy[1]:.3f}  yaw={n.msg.imu_state.rpy[2]:.3f}")
        print(f"Mode: {n.msg.mode_machine}")
    else:
        print("ERROR: No LowState received - is robot on and ethernet connected?")
    rclpy.shutdown()
except Exception as e:
    print(f"ERROR: {e}")
PYEOF

echo ""
echo "=== 5. LiDAR Point Cloud Check ==="
python3 - <<'PYEOF'
import sys, struct, numpy as np
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy
    from sensor_msgs.msg import PointCloud2

    rclpy.init()
    class LidarCheck(Node):
        def __init__(self):
            super().__init__('lidar_check')
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.cloud = None
            self.create_subscription(PointCloud2, '/utlidar/cloud_livox_mid360', lambda m: setattr(self, 'cloud', m), qos)

    n = LidarCheck()
    for _ in range(50):
        rclpy.spin_once(n, timeout_sec=0.1)
        if n.cloud:
            break

    if n.cloud:
        total = n.cloud.width * n.cloud.height
        print(f"LiDAR: {total} points per scan  frame={n.cloud.header.frame_id}")
        print("LiDAR OK - ready for object detection")
    else:
        print("No LiDAR data - check /utlidar/cloud_livox_mid360 topic")
    rclpy.shutdown()
except Exception as e:
    print(f"ERROR: {e}")
PYEOF

echo ""
echo "=== Done. Check above for any ERRORs ==="
```
