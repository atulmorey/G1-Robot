#!/usr/bin/env python3
META = {
    "name": "Touch Object",
    "icon": "🫳",
    "description": "Detects object on table and reaches right arm to touch it.",
}

import sys
import time
import struct
import numpy as np

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import PointCloud2
        from unitree_hg.msg import LowCmd, LowState
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

# ── ROI ──────────────────────────────────────────────────────────
ROI_X_MIN = -2.0; ROI_X_MAX = 1.0
ROI_Y_MIN = -3.0; ROI_Y_MAX = 3.0
ROI_Z_MIN = 0.2;  ROI_Z_MAX = 1.2
MIN_CLUSTER_POINTS = 30

# ── Joint indices (robot perspective) ────────────────────────────
# From g1.hpp: LEFT = joints 15-19, RIGHT = joints 22-26
RIGHT_SHOULDER_PITCH = 22
RIGHT_SHOULDER_ROLL  = 23
RIGHT_SHOULDER_YAW   = 24
RIGHT_ELBOW          = 25

# kp/kd from official arm SDK example
KP = 60.0
KD = 1.5


def calc_crc(cmd):
    d = struct.pack('BBxx', cmd.mode_pr, cmd.mode_machine)
    for m in cmd.motor_cmd:
        d += struct.pack('BxxxfffffI', m.mode, m.q, m.dq, m.tau, m.kp, m.kd, m.reserve)
    d += struct.pack('4I', *cmd.reserve[:4])
    words = struct.unpack(str(len(d) // 4) + 'I', d)
    crc = 0xFFFFFFFF
    poly = 0x04c11db7
    for w in words:
        xbit = 1 << 31
        for _ in range(32):
            crc = (((crc << 1) & 0xFFFFFFFF) ^ poly) if (crc & 0x80000000) else ((crc << 1) & 0xFFFFFFFF)
            if w & xbit:
                crc ^= poly
            xbit >>= 1
    return crc


def parse_pointcloud2(msg):
    points = []
    offsets = {}
    for field in msg.fields:
        if field.name in ('x', 'y', 'z'):
            offsets[field.name] = field.offset
    if not all(k in offsets for k in ('x', 'y', 'z')):
        return np.array([])
    ox, oy, oz = offsets['x'], offsets['y'], offsets['z']
    for i in range(msg.width * msg.height):
        base = i * msg.point_step
        x = struct.unpack_from('f', msg.data, base + ox)[0]
        y = struct.unpack_from('f', msg.data, base + oy)[0]
        z = struct.unpack_from('f', msg.data, base + oz)[0]
        if not (np.isnan(x) or np.isnan(y) or np.isnan(z)):
            points.append([x, y, z])
    return np.array(points) if points else np.array([])


def find_best_target(points):
    mask = (
        (points[:, 0] >= ROI_X_MIN) & (points[:, 0] <= ROI_X_MAX) &
        (points[:, 1] >= ROI_Y_MIN) & (points[:, 1] <= ROI_Y_MAX) &
        (points[:, 2] >= ROI_Z_MIN) & (points[:, 2] <= ROI_Z_MAX)
    )
    roi = points[mask]
    if len(roi) < MIN_CLUSTER_POINTS:
        return None
    best = None
    best_size = 0
    used = np.zeros(len(roi), dtype=bool)
    for i in range(len(roi)):
        if used[i]:
            continue
        dists = np.linalg.norm(roi - roi[i], axis=1)
        cm = dists < 0.15
        if cm.sum() >= MIN_CLUSTER_POINTS and cm.sum() > best_size:
            best_size = int(cm.sum())
            best = roi[cm].mean(axis=0)
            used[cm] = True
    return best


def main():
    if OFFLINE:
        print("OFFLINE: Simulating touch...")
        print("  Target: x=0.15m  y=-0.84m  z=0.82m")
        print("  Moving right arm to target...")
        time.sleep(2)
        print("  Touch complete!")
        return

    rclpy.init()

    class TouchNode(Node):
        def __init__(self):
            super().__init__("touch_object_node")
            qos_be = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.arm_pub = self.create_publisher(LowCmd, "/armsdk", qos_be)
            self.latest_cloud = None
            self.current_jpos = {}
            self.state_received = False
            self.create_subscription(PointCloud2, "/utlidar/cloud_livox_mid360",
                                     lambda m: setattr(self, 'latest_cloud', m), qos_be)
            self.create_subscription(LowState, "/lf/lowstate", self._state_cb, qos_be)

        def _state_cb(self, msg):
            for idx in [RIGHT_SHOULDER_PITCH, RIGHT_SHOULDER_ROLL,
                        RIGHT_SHOULDER_YAW, RIGHT_ELBOW]:
                self.current_jpos[idx] = msg.motor_state[idx].q
            self.state_received = True

        def interpolate_to(self, target_joints, duration=3.0, steps=150):
            """Interpolate from current positions to target — mirrors official SDK approach."""
            start_pos = dict(self.current_jpos)
            dt = duration / steps
            for i in range(steps):
                alpha = i / steps
                cmd = LowCmd()
                cmd.mode_machine = 5
                for j, q_target in target_joints.items():
                    q_start = start_pos.get(j, 0.0)
                    cmd.motor_cmd[j].mode = 1
                    cmd.motor_cmd[j].q    = q_start + alpha * (q_target - q_start)
                    cmd.motor_cmd[j].dq   = 0.0
                    cmd.motor_cmd[j].kp   = KP
                    cmd.motor_cmd[j].kd   = KD
                cmd.crc = calc_crc(cmd)
                self.arm_pub.publish(cmd)
                time.sleep(dt)

    node = TouchNode()

    # Wait for LowState — matches official SDK "Waiting for LowState..."
    print("Waiting for LowState...")
    start = time.time()
    while not node.state_received and (time.time() - start) < 8.0:
        rclpy.spin_once(node, timeout_sec=0.1)
    if not node.state_received:
        print("No robot state — is robot on?")
        rclpy.shutdown()
        sys.exit(1)
    print(f"LowState received. Current right arm: {node.current_jpos}")

    # Scan for objects
    print("Scanning for objects...")
    for _ in range(20):
        rclpy.spin_once(node, timeout_sec=0.2)
        if node.latest_cloud:
            break
    if node.latest_cloud is None:
        print("No LiDAR data.")
        rclpy.shutdown()
        sys.exit(1)

    points = parse_pointcloud2(node.latest_cloud)
    target = find_best_target(points)
    if target is None:
        print("No object detected — point robot toward table.")
        rclpy.shutdown()
        sys.exit(1)

    tx, ty, tz = float(target[0]), float(target[1]), float(target[2])
    print(f"Target: x={tx:.2f}m  y={ty:.2f}m  z={tz:.2f}m")

    # Calculate target joint angles for right arm
    # Right shoulder roll is negative for right arm reaching out
    reach_joints = {
        RIGHT_SHOULDER_PITCH: float(np.clip(0.3 + (tz - 0.9) * 0.5,  -0.3, 0.8)),
        RIGHT_SHOULDER_ROLL:  float(np.clip(-0.3 + ty * 0.1,          -0.8, -0.1)),
        RIGHT_SHOULDER_YAW:   float(np.clip(tx * 0.15,                -0.3,  0.3)),
        RIGHT_ELBOW:          float(np.clip(0.5 + (1.2 - tz) * 0.4,   0.1,  1.2)),
    }
    print(f"Target joints: pitch={reach_joints[RIGHT_SHOULDER_PITCH]:.3f} "
          f"roll={reach_joints[RIGHT_SHOULDER_ROLL]:.3f} "
          f"elbow={reach_joints[RIGHT_ELBOW]:.3f}")

    # Move to target
    print("Moving right arm to target...")
    node.interpolate_to(reach_joints, duration=3.0)

    print("Holding 1 second...")
    time.sleep(1.0)

    # Return home
    print("Returning to home...")
    home = {j: 0.0 for j in reach_joints}
    node.interpolate_to(home, duration=3.0)

    print("Touch complete!")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
