#!/usr/bin/env python3
META = {
    "name": "Joint Map",
    "icon": "🗺",
    "description": "Prints all 29 joint positions, velocities, torques and full IMU state.",
}

import sys
import math

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_hg.msg import LowState
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

JOINT_NAMES = [
    "L_hip_pitch", "L_hip_roll", "L_hip_yaw", "L_knee", "L_ankle_pitch", "L_ankle_roll",
    "R_hip_pitch", "R_hip_roll", "R_hip_yaw", "R_knee", "R_ankle_pitch", "R_ankle_roll",
    "waist_yaw", "waist_roll", "waist_pitch",
    "L_shoulder_pitch", "L_shoulder_roll", "L_shoulder_yaw", "L_elbow", "L_wrist_roll", "L_wrist_pitch", "L_wrist_yaw",
    "R_shoulder_pitch", "R_shoulder_roll", "R_shoulder_yaw", "R_elbow", "R_wrist_roll", "R_wrist_pitch", "R_wrist_yaw",
]

GROUPS = [
    ("LEFT LEG",  range(0, 6)),
    ("RIGHT LEG", range(6, 12)),
    ("WAIST",     range(12, 15)),
    ("LEFT ARM",  range(15, 22)),
    ("RIGHT ARM", range(22, 29)),
]


def print_table(motor_state):
    header = f"{'IDX':>3}  {'NAME':<22}  {'q(rad)':>8}  {'q(deg)':>8}  {'dq(r/s)':>8}  {'tau_est(Nm)':>11}"
    sep = "-" * len(header)
    for group_name, indices in GROUPS:
        print(f"\n  -- {group_name} --")
        print(f"  {header}")
        print(f"  {sep}")
        for i in indices:
            if i >= len(motor_state):
                continue
            m = motor_state[i]
            tau = float(getattr(m, "tau_est", getattr(m, "tau", 0.0)))
            name = JOINT_NAMES[i] if i < len(JOINT_NAMES) else f"joint_{i}"
            print(f"  {i:>3}  {name:<22}  {float(m.q):>8.4f}  {math.degrees(float(m.q)):>8.2f}  {float(m.dq):>8.4f}  {tau:>11.3f}")


def print_imu(imu):
    print("\n  -- IMU --")
    print(f"  RPY : roll={float(imu.rpy[0]):>8.4f}  pitch={float(imu.rpy[1]):>8.4f}  yaw={float(imu.rpy[2]):>8.4f}  rad")
    print(f"  ACC : x={float(imu.acc[0]):>8.4f}   y={float(imu.acc[1]):>8.4f}   z={float(imu.acc[2]):>8.4f}  m/s^2")
    print(f"  GYRO: x={float(imu.gyro[0]):>8.4f}   y={float(imu.gyro[1]):>8.4f}   z={float(imu.gyro[2]):>8.4f}  rad/s")


def main():
    if OFFLINE:
        print("OFFLINE MODE — showing zero-state table\n")

        class FakeMotor:
            q = 0.0; dq = 0.0; tau_est = 0.0

        class FakeIMU:
            rpy = [0.051, -0.044, 2.151]
            acc  = [0.0, 0.0, 9.81]
            gyro = [0.0, 0.0, 0.0]

        print_table([FakeMotor()] * 29)
        print_imu(FakeIMU())
        return

    rclpy.init()

    class MapNode(Node):
        def __init__(self):
            super().__init__("show_joint_map")
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.msg = None
            self.create_subscription(LowState, "/lf/lowstate",
                                     lambda m: setattr(self, "msg", m), qos)

    node = MapNode()
    print("Waiting for LowState...")
    for _ in range(80):
        rclpy.spin_once(node, timeout_sec=0.1)
        if node.msg:
            break

    if not node.msg:
        print("ERROR: No LowState received — is the robot on?")
        rclpy.shutdown()
        return

    print(f"\n=== G1 JOINT MAP  (mode_machine={node.msg.mode_machine}) ===")
    print_table(node.msg.motor_state)
    print_imu(node.msg.imu_state)
    print()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
