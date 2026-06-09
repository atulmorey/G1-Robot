#!/usr/bin/env python3
"""
G1 Touch Planner — Day 3
Reads object position from LiDAR, plans arm path to touch it.
Run:
  source ~/unitree_ros2/setup.sh
  source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
  python3 ~/G1-Robot/g1_plan_touch.py
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointCloud2
from unitree_hg.msg import LowCmd, LowState
import numpy as np
import struct
import time
import threading

# ── ROI (same as g1_detect_objects.py) ─────────────────────────
ROI_X_MIN = -0.2
ROI_X_MAX = 0.8
ROI_Y_MIN = -1.6
ROI_Y_MAX = -0.7
ROI_Z_MIN = 0.15
ROI_Z_MAX = 0.6
MIN_CLUSTER_POINTS = 30

# ── Arm joints for left arm touch ───────────────────────────────
# Joint indices from LowState motor_state array
LEFT_SHOULDER_PITCH = 15
LEFT_SHOULDER_ROLL  = 16
LEFT_SHOULDER_YAW   = 17
LEFT_ELBOW          = 18

# ── CRC ─────────────────────────────────────────────────────────
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
    point_step = msg.point_step
    data = msg.data
    offsets = {}
    for field in msg.fields:
        if field.name in ('x', 'y', 'z'):
            offsets[field.name] = field.offset
    if not all(k in offsets for k in ('x', 'y', 'z')):
        return np.array([])
    ox, oy, oz = offsets['x'], offsets['y'], offsets['z']
    for i in range(msg.width * msg.height):
        base = i * point_step
        x = struct.unpack_from('f', data, base + ox)[0]
        y = struct.unpack_from('f', data, base + oy)[0]
        z = struct.unpack_from('f', data, base + oz)[0]
        if not (np.isnan(x) or np.isnan(y) or np.isnan(z)):
            points.append([x, y, z])
    return np.array(points) if points else np.array([])


def find_best_target(points):
    """Find the largest cluster above table — best touch target."""
    if len(points) == 0:
        return None
    mask = (
        (points[:, 0] >= ROI_X_MIN) & (points[:, 0] <= ROI_X_MAX) &
        (points[:, 1] >= ROI_Y_MIN) & (points[:, 1] <= ROI_Y_MAX) &
        (points[:, 2] >= ROI_Z_MIN) & (points[:, 2] <= ROI_Z_MAX)
    )
    roi = points[mask]
    if len(roi) < MIN_CLUSTER_POINTS:
        return None

    # Find largest cluster
    best = None
    best_size = 0
    used = np.zeros(len(roi), dtype=bool)
    for i in range(len(roi)):
        if used[i]:
            continue
        dists = np.linalg.norm(roi - roi[i], axis=1)
        cluster_mask = dists < 0.15
        if cluster_mask.sum() >= MIN_CLUSTER_POINTS:
            size = cluster_mask.sum()
            if size > best_size:
                best_size = size
                best = roi[cluster_mask].mean(axis=0)
            used[cluster_mask] = True

    return best


def lidar_to_joint_angles(target):
    """
    Convert LiDAR target position to approximate arm joint angles.
    This is a simplified inverse kinematics for the G1 left arm.
    target: [x, y, z] in LiDAR frame
    Returns: dict of joint_index -> target_angle
    """
    tx, ty, tz = target

    # The table is at y≈-1.2m in LiDAR frame
    # Map to approximate shoulder angles
    # shoulder_pitch: controls forward/backward reach
    # shoulder_roll: controls left/right reach

    # Normalize distance — table is ~0.56m away
    dist = np.sqrt(tx**2 + ty**2)

    # Shoulder pitch — reach forward (positive = forward)
    shoulder_pitch = np.clip(0.3 + tz * 0.5, 0.1, 0.8)

    # Shoulder roll — reach sideways toward object
    shoulder_roll = np.clip(ty * 0.3 + 0.2, 0.1, 0.6)

    # Elbow — bend more for closer objects
    elbow = np.clip(0.8 - dist * 0.3, 0.3, 1.2)

    return {
        LEFT_SHOULDER_PITCH: shoulder_pitch,
        LEFT_SHOULDER_ROLL:  shoulder_roll,
        LEFT_ELBOW:          elbow,
    }


class TouchPlanner(Node):
    def __init__(self):
        super().__init__("touch_planner")
        qos_be  = QoSProfile(depth=1,  reliability=ReliabilityPolicy.BEST_EFFORT)
        qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        self.arm_pub = self.create_publisher(LowCmd, "/armsdk", qos_be)
        self.latest_cloud = None
        self.latest_state = None
        self.cloud_lock = threading.Lock()

        self.create_subscription(PointCloud2, "/utlidar/cloud_livox_mid360",
                                 self._cloud_cb, qos_be)
        self.create_subscription(LowState, "/lf/lowstate",
                                 self._state_cb, qos_be)
        print("Touch planner ready. Waiting for robot state and point cloud...")

    def _cloud_cb(self, msg):
        with self.cloud_lock:
            self.latest_cloud = msg

    def _state_cb(self, msg):
        self.latest_state = msg

    def wait_ready(self, timeout=10.0):
        start = time.time()
        while (time.time() - start) < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.latest_cloud and self.latest_state:
                return True
        return False

    def detect_target(self):
        rclpy.spin_once(self, timeout_sec=0.5)
        with self.cloud_lock:
            if not self.latest_cloud:
                return None
            points = parse_pointcloud2(self.latest_cloud)
        return find_best_target(points)

    def send_joints(self, joint_angles, duration=3.0, steps=60):
        cmd = LowCmd()
        cmd.mode_machine = 5
        for joint_idx, target_q in joint_angles.items():
            cmd.motor_cmd[joint_idx].mode = 1
            cmd.motor_cmd[joint_idx].q = target_q
            cmd.motor_cmd[joint_idx].kp = 60.0
            cmd.motor_cmd[joint_idx].kd = 2.0
        dt = duration / steps
        for _ in range(steps):
            cmd.crc = calc_crc(cmd)
            self.arm_pub.publish(cmd)
            time.sleep(dt)

    def return_home(self, duration=3.0):
        home = {
            LEFT_SHOULDER_PITCH: 0.0,
            LEFT_SHOULDER_ROLL:  0.0,
            LEFT_SHOULDER_YAW:   0.0,
            LEFT_ELBOW:          0.0,
        }
        self.send_joints(home, duration=duration)

    def touch_object(self):
        print("\n=== Scanning for objects ===")
        target = self.detect_target()
        if target is None:
            print("No object detected in ROI. Point robot toward table.")
            return False

        print(f"Target found: x={target[0]:.2f}m  y={target[1]:.2f}m  z={target[2]:.2f}m")

        joint_angles = lidar_to_joint_angles(target)
        print(f"Planned joint angles:")
        for j, a in joint_angles.items():
            print(f"  Joint {j}: {a:.3f} rad")

        print("\nMoving arm to target...")
        self.send_joints(joint_angles, duration=3.0)

        print("Holding position 1 second...")
        time.sleep(1.0)

        print("Returning to home position...")
        self.return_home(duration=3.0)

        print("Touch complete!")
        return True


def main():
    rclpy.init()
    node = TouchPlanner()

    print("Waiting for robot state and point cloud (10s)...")
    if not node.wait_ready(timeout=10.0):
        print("Timeout — check robot is on and connected")
        rclpy.shutdown()
        return

    print("Robot ready!")
    print("\nStarting touch sequence in 3 seconds...")
    print("Make sure robot is in STANDING mode before continuing!")
    time.sleep(3.0)

    node.touch_object()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
