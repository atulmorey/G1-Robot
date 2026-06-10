#!/usr/bin/env python3
META = {
    "name": "Monitor Events",
    "icon": "📡",
    "description": "Live robot state — mode, IMU, arm joints every 2s. Press Stop to end.",
}

import sys
import time

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

MODE_NAMES = {
    0: "IDLE", 1: "BALANCE_STAND", 2: "POSE", 3: "LOCOMOTION",
    5: "JOINT_LOCK", 6: "DAMPING", 7: "RECOVERY_STAND", 9: "SIT"
}


def ts():
    return time.strftime("%H:%M:%S")


def main():
    if OFFLINE:
        print(f"[{ts()}] OFFLINE mode — simulated:")
        for i in range(5):
            time.sleep(2)
            print(f"[{ts()}] JOINT_LOCK  pitch=-0.04  L_arm=0.08  R_arm=-0.09")
        return

    rclpy.init()

    class MonitorNode(Node):
        def __init__(self):
            super().__init__("monitor_events_node")
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.state = None
            self.prev_mode = None
            self.prev_la = None
            self.create_subscription(LowState, "/lf/lowstate",
                                     lambda m: setattr(self, 'state', m), qos)
            print(f"[{ts()}] Monitoring robot via /lf/lowstate every 2s")

        def print_state(self):
            if not self.state:
                print(f"[{ts()}] No data — is robot connected?")
                return
            s = self.state
            mode = int(s.mode_machine)
            mode_name = MODE_NAMES.get(mode, f"mode_{mode}")
            pitch = round(s.imu_state.rpy[1], 3)
            roll  = round(s.imu_state.rpy[0], 3)
            la = round(s.motor_state[15].q, 3)
            ra = round(s.motor_state[22].q, 3)

            if mode != self.prev_mode:
                print(f"[{ts()}] *** MODE CHANGE → {mode_name} ({mode}) ***")
                self.prev_mode = mode

            if self.prev_la is None or abs(la - self.prev_la) > 0.05:
                print(f"[{ts()}] ARM MOVED  L={la}  R={ra}")
                self.prev_la = la

            print(f"[{ts()}] {mode_name}  pitch={pitch}  roll={roll}  L={la}  R={ra}")

    node = MonitorNode()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=2.0)
            node.print_state()
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()


if __name__ == "__main__":
    main()
