#!/usr/bin/env python3
META = {
    "name": "Wave Right Arm",
    "icon": "🤚",
    "description": "Raise and return right shoulder (joint 22).",
}

import sys
import time
import struct

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_hg.msg import LowCmd, LowState
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

JOINT_IDX = 22
TARGET_Q  = -0.8


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


def main():
    if OFFLINE:
        print("OFFLINE: Raising right arm (joint 22) to -0.8 rad...")
        time.sleep(1)
        print("OFFLINE: Returning to home...")
        time.sleep(1)
        print("Done.")
        return

    rclpy.init()

    class ArmNode(Node):
        def __init__(self):
            super().__init__("wave_right_arm_node")
            qos_be = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.arm_pub = self.create_publisher(LowCmd, "/armsdk", qos_be)
            self.latest_state = None
            self.create_subscription(LowState, "/lf/lowstate", self._cb, qos_be)

        def _cb(self, msg):
            self.latest_state = msg

        def wait_for_state(self, timeout=3.0):
            start = time.time()
            while self.latest_state is None and (time.time() - start) < timeout:
                rclpy.spin_once(self, timeout_sec=0.1)
            return self.latest_state

    node = ArmNode()
    state = node.wait_for_state()

    if not state:
        print("No robot state received — is the robot on?")
        rclpy.shutdown()
        sys.exit(1)

    if state.mode_machine != 5:
        print(f"Robot not in standing mode (mode={state.mode_machine}). Run Stand Up first.")
        rclpy.shutdown()
        sys.exit(1)

    cmd = LowCmd()
    cmd.mode_machine = 5
    cmd.motor_cmd[JOINT_IDX].mode = 1
    cmd.motor_cmd[JOINT_IDX].kp   = 80.0
    cmd.motor_cmd[JOINT_IDX].kd   = 2.0

    print(f"Raising right arm to {TARGET_Q} rad...")
    cmd.motor_cmd[JOINT_IDX].q = TARGET_Q
    for i in range(50):
        cmd.crc = calc_crc(cmd)
        node.arm_pub.publish(cmd)
        time.sleep(0.05)

    print("Returning to home position...")
    cmd.motor_cmd[JOINT_IDX].q = 0.0
    for i in range(50):
        cmd.crc = calc_crc(cmd)
        node.arm_pub.publish(cmd)
        time.sleep(0.05)

    print("Done.")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
