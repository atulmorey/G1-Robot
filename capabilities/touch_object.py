#!/usr/bin/env python3
META = {
    "name": "Touch Object",
    "icon": "🫳",
    "description": "Detects nearest object on table and touches it with left arm.",
}

import sys
import time
import struct
import json
import numpy as np

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import PointCloud2
        from unitree_hg.msg import LowCmd, LowState
        from unitree_api.msg import Request, Response
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

# ── ROI ──────────────────────────────────────────────────────────
ROI_X_MIN = -2.0
ROI_X_MAX = 1.0
ROI_Y_MIN = -3.0
ROI_Y_MAX = 3.0
ROI_Z_MIN = 0.2
ROI_Z_MAX = 1.2
MIN_CLUSTER_POINTS = 30

# ── Known arm positions from task_id=2 ──────────────────────────
LEFT_SHOULDER_PITCH = 15
LEFT_SHOULDER_ROLL  = 16
LEFT_SHOULDER_YAW   = 17
LEFT_ELBOW          = 18

ARM_TASK_2_JOINTS = {
    LEFT_SHOULDER_PITCH: 0.292,
    LEFT_SHOULDER_ROLL:  0.218,
    LEFT_SHOULDER_YAW:  -0.012,
    LEFT_ELBOW:          0.979,
}

LOCO_SET_ARM_TASK = 7106


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
            best_size = cm.sum()
            best = roi[cm].mean(axis=0)
            used[cm] = True
    return best


def main():
    if OFFLINE:
        print("OFFLINE: Simulating touch sequence...")
        print("  Target: x=-0.21m  y=-1.06m  z=1.10m")
        print("  Activating arm via task_id=2...")
        time.sleep(1)
        print("  Returning home...")
        time.sleep(1)
        print("  Touch complete!")
        return

    rclpy.init()

    class TouchNode(Node):
        def __init__(self):
            super().__init__("touch_object_node")
            qos_be  = QoSProfile(depth=1,  reliability=ReliabilityPolicy.BEST_EFFORT)
            qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            self.arm_pub   = self.create_publisher(LowCmd, "/armsdk", qos_be)
            self.sport_pub = self.create_publisher(Request, "/api/sport/request", qos_rel)
            self.latest_cloud = None
            self.latest_state = None
            self.sport_resp   = None
            self.create_subscription(PointCloud2, "/utlidar/cloud_livox_mid360",
                                     lambda m: setattr(self, 'latest_cloud', m), qos_be)
            self.create_subscription(LowState, "/lf/lowstate",
                                     lambda m: setattr(self, 'latest_state', m), qos_be)
            self.create_subscription(Response, "/api/sport/response",
                                     lambda m: setattr(self, 'sport_resp', m), qos_be)

        def send_arm_task(self, task_id):
            msg = Request()
            msg.header.identity.api_id = LOCO_SET_ARM_TASK
            msg.parameter = json.dumps({"data": task_id})
            self.sport_resp = None
            self.sport_pub.publish(msg)
            start = time.time()
            while self.sport_resp is None and (time.time() - start) < 3.0:
                rclpy.spin_once(self, timeout_sec=0.1)
            code = self.sport_resp.header.status.code if self.sport_resp else "timeout"
            return code

        def send_joints(self, joint_angles, duration=3.0, steps=60):
            cmd = LowCmd()
            cmd.mode_machine = 5
            for j, q in joint_angles.items():
                cmd.motor_cmd[j].mode = 1
                cmd.motor_cmd[j].q    = q
                cmd.motor_cmd[j].kp   = 60.0
                cmd.motor_cmd[j].kd   = 2.0
            dt = duration / steps
            for _ in range(steps):
                cmd.crc = calc_crc(cmd)
                self.arm_pub.publish(cmd)
                time.sleep(dt)

    node = TouchNode()

    print("Waiting for robot state...")
    start = time.time()
    while node.latest_state is None and (time.time() - start) < 8.0:
        rclpy.spin_once(node, timeout_sec=0.1)
    if node.latest_state is None:
        print("No robot state — is robot on?")
        rclpy.shutdown()
        sys.exit(1)

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

    print(f"Target: x={target[0]:.2f}m  y={target[1]:.2f}m  z={target[2]:.2f}m")

    # Step 1 — activate arm via sport API task_id=2
    print("Activating arm (task_id=2)...")
    code = node.send_arm_task(2)
    print(f"Arm task response: {code}")
    time.sleep(1.5)

    # Step 2 — fine-tune toward object using known task_id=2 joint positions as base
    # Adjust shoulder pitch based on object Z height relative to arm position
    joints = dict(ARM_TASK_2_JOINTS)
    tz = float(target[2])
    ty = float(target[1])

    # Adjust pitch down/up based on object height difference from arm rest position
    joints[LEFT_SHOULDER_PITCH] = float(np.clip(0.292 + (tz - 1.0) * 0.3, 0.0, 0.8))
    joints[LEFT_SHOULDER_ROLL]  = float(np.clip(0.218 - ty * 0.1, 0.1, 0.6))

    print(f"Fine-tuned joints: pitch={joints[LEFT_SHOULDER_PITCH]:.3f}  roll={joints[LEFT_SHOULDER_ROLL]:.3f}")
    print("Moving arm to target...")
    node.send_joints(joints, duration=2.0)

    print("Holding 1 second...")
    time.sleep(1.0)

    print("Returning home (task_id=0)...")
    code = node.send_arm_task(0)
    print(f"Home response: {code}")
    time.sleep(1.0)

    print("Touch complete!")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
