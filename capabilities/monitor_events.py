#!/usr/bin/env python3
META = {
    "name": "Monitor Events",
    "icon": "📡",
    "description": "Live robot state — mode, velocity, gait, arm joints every 2s.",
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
        from unitree_api.msg import Request, Response
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

SPORT_API_NAMES = {
    1001: "CHECK_MODE", 1002: "SELECT_MODE", 1003: "RELEASE_MODE",
    1004: "STAND_UP", 1005: "STOP_MOVE", 1006: "BALANCE_STAND",
    1007: "DAMP", 1008: "RECOVERY_STAND", 1009: "SIT",
    1016: "HELLO/WAVE", 1017: "STRETCH", 1019: "SCRAPE",
    1020: "FRONT_FLIP", 1021: "FRONT_JUMP",
    7101: "SET_FSM_ID", 7105: "SET_VELOCITY", 7106: "ARM_TASK",
}


def ts():
    return time.strftime("%H:%M:%S")


def main():
    if OFFLINE:
        print(f"[{ts()}] OFFLINE — simulated events:")
        for i in range(5):
            time.sleep(2)
            print(f"[{ts()}] JOINT_LOCK  L_arm=0.08  R_arm=-0.09")
        return

    rclpy.init()

    class MonitorNode(Node):
        def __init__(self):
            super().__init__("monitor_events_node")
            qos_be  = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            self.state = None
            self.prev_mode = None
            self.prev_joints = None

            self.create_subscription(LowState, "/lf/lowstate", self._state_cb, qos_be)
            self.create_subscription(Request, "/api/sport/request",
                self._sport_req_cb, qos_rel)
            self.create_subscription(Request, "/api/motion_switcher/request",
                self._switch_req_cb, qos_rel)

            print(f"[{ts()}] Monitoring started — watching state + API calls")

        def _state_cb(self, msg):
            self.state = msg

        def _sport_req_cb(self, msg):
            api_id = msg.header.identity.api_id
            name = SPORT_API_NAMES.get(api_id, f"api_id={api_id}")
            print(f"[{ts()}] → SPORT API: {name} ({api_id})")

        def _switch_req_cb(self, msg):
            api_id = msg.header.identity.api_id
            name = SPORT_API_NAMES.get(api_id, f"api_id={api_id}")
            param = msg.parameter[:40] if msg.parameter else ""
            print(f"[{ts()}] → SWITCHER: {name} {param}")

        def print_state(self):
            if not self.state:
                print(f"[{ts()}] No data — is robot connected?")
                return
            s = self.state
            mode = int(s.mode_machine)
            mode_name = MODE_NAMES.get(mode, f"mode_{mode}")
            ls = round(s.motor_state[15].q, 3)
            rs = round(s.motor_state[22].q, 3)
            pitch = round(s.imu_state.rpy[1], 3)

            if mode != self.prev_mode:
                print(f"[{ts()}] *** MODE → {mode_name} ({mode}) ***")
                self.prev_mode = mode

            joints = (ls, rs)
            if joints != self.prev_joints:
                print(f"[{ts()}] ARM: L={ls}  R={rs}  pitch={pitch}")
                self.prev_joints = joints

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
