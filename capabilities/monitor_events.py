#!/usr/bin/env python3
META = {
    "name": "Monitor Events",
    "icon": "📡",
    "description": "Live robot state — walking mode, velocity, gait, arm joints.",
}

import sys
import time

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_go.msg import SportModeState
        from unitree_hg.msg import LowState
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

SPORT_MODES = {
    0: "IDLE", 1: "BALANCE_STAND", 2: "POSE", 3: "LOCOMOTION",
    5: "LIE_DOWN", 6: "JOINT_LOCK", 7: "DAMPING", 8: "RECOVERY_STAND",
    9: "RESERVE", 10: "SIT", 11: "FRONT_FLIP", 12: "FRONT_JUMP",
}

GAIT_TYPES = {
    0: "idle", 1: "trot", 2: "run", 3: "climb_stair",
    4: "forward_down_stair", 9: "adjust"
}


def ts():
    return time.strftime("%H:%M:%S")


def main():
    if OFFLINE:
        print(f"[{ts()}] OFFLINE — simulated events:")
        for i in range(5):
            time.sleep(2)
            print(f"[{ts()}] BALANCE_STAND  vx=0.00  vy=0.00  gait=idle  L_arm=0.08")
        return

    rclpy.init()

    class MonitorNode(Node):
        def __init__(self):
            super().__init__("monitor_events_node")
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.sport = None
            self.low = None
            self.prev_mode = None
            self.prev_gait = None

            self.create_subscription(SportModeState, "/lf/sportmodestate",
                                     lambda m: setattr(self, 'sport', m), qos)
            self.create_subscription(LowState, "/lf/lowstate",
                                     lambda m: setattr(self, 'low', m), qos)
            print(f"[{ts()}] Monitoring started — robot state every 2s")

        def print_state(self):
            if not self.sport:
                print(f"[{ts()}] No sport data yet...")
                return

            s = self.sport
            mode = int(s.mode)
            gait = int(s.gait_type)
            mode_name = SPORT_MODES.get(mode, f"mode_{mode}")
            gait_name = GAIT_TYPES.get(gait, f"gait_{gait}")
            vx = round(s.velocity[0], 3)
            vy = round(s.velocity[1], 3)
            omega = round(s.yaw_speed, 3)
            height = round(s.body_height, 3)

            # Arm joints from LowState
            la = round(self.low.motor_state[15].q, 3) if self.low else "?"
            ra = round(self.low.motor_state[22].q, 3) if self.low else "?"

            if mode != self.prev_mode:
                print(f"[{ts()}] *** MODE → {mode_name} ({mode}) ***")
                self.prev_mode = mode

            if gait != self.prev_gait:
                print(f"[{ts()}] *** GAIT → {gait_name} ({gait}) ***")
                self.prev_gait = gait

            print(f"[{ts()}] {mode_name}  vx={vx}  vy={vy}  ω={omega}  "
                  f"gait={gait_name}  h={height}  L_arm={la}  R_arm={ra}")

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
