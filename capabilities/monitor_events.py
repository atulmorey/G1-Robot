#!/usr/bin/env python3
META = {
    "name": "Monitor Events",
    "icon": "📡",
    "description": "Live feed of robot API calls and responses. Press Stop to end.",
}

import sys
import time
import json

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_api.msg import Request, Response
        from unitree_hg.msg import LowState
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

# Human-readable API ID names
SPORT_API_NAMES = {
    1001: "CHECK_MODE",
    1002: "SELECT_MODE",
    1003: "RELEASE_MODE",
    1016: "HELLO/WAVE",
    1009: "SIT",
    1004: "STAND_UP",
    1008: "RECOVERY_STAND",
    1007: "DAMP",
    1005: "STOP_MOVE",
    1006: "BALANCE_STAND",
    7001: "LOCO_GET_FSM_ID",
    7002: "LOCO_GET_FSM_MODE",
    7003: "LOCO_GET_BALANCE_MODE",
    7101: "LOCO_SET_FSM_ID",
    7102: "LOCO_SET_BALANCE_MODE",
    7105: "LOCO_SET_VELOCITY",
    7106: "LOCO_SET_ARM_TASK",
}

RESPONSE_CODES = {
    0: "OK",
    -1: "TIMEOUT",
    7002: "INVALID_MODE",
    7004: "MODE_NOT_FOUND",
    7301: "LOCOSTATE_NOT_AVAILABLE",
    7302: "INVALID_FSM_ID",
}


def ts():
    return time.strftime("%H:%M:%S")


def format_request(msg, topic):
    api_id = msg.header.identity.api_id
    name = SPORT_API_NAMES.get(api_id, f"api_id={api_id}")
    param = ""
    if msg.parameter:
        try:
            p = json.loads(msg.parameter)
            param = f" | {p}"
        except Exception:
            param = f" | {msg.parameter[:40]}"
    topic_short = topic.replace("/api/", "").replace("/request", "").upper()
    return f"[{ts()}] ← {topic_short}  {name}{param}"


def format_response(msg, topic):
    code = msg.header.status.code
    status = RESPONSE_CODES.get(code, f"code={code}")
    data = f" | {msg.data[:60]}" if msg.data else ""
    topic_short = topic.replace("/api/", "").replace("/response", "").upper()
    color = "✓" if code == 0 else "✗"
    return f"[{ts()}] {color} {topic_short}  {status}{data}"


def main():
    if OFFLINE:
        print("OFFLINE: Simulating robot events...")
        events = [
            "[13:05:10] ← SPORT  HELLO/WAVE",
            "[13:05:10] ✓ SPORT  OK",
            "[13:05:15] ← MOTION_SWITCHER  CHECK_MODE",
            "[13:05:15] ✓ MOTION_SWITCHER  OK | {\"name\":\"ai\"}",
            "[13:05:20] ← SPORT  DAMP",
            "[13:05:20] ✓ SPORT  OK",
        ]
        for e in events:
            print(e)
            time.sleep(1)
        print("(Offline demo complete — showing real events when live)")
        return

    rclpy.init()

    class MonitorNode(Node):
        def __init__(self):
            super().__init__("monitor_events_node")
            qos_be  = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

            self.create_subscription(Request,  "/api/sport/request",
                lambda m: print(format_request(m, "/api/sport/request")), qos_be)
            self.create_subscription(Response, "/api/sport/response",
                lambda m: print(format_response(m, "/api/sport/response")), qos_be)
            self.create_subscription(Request,  "/api/motion_switcher/request",
                lambda m: print(format_request(m, "/api/motion_switcher/request")), qos_be)
            self.create_subscription(Response, "/api/motion_switcher/response",
                lambda m: print(format_response(m, "/api/motion_switcher/response")), qos_be)
            self.create_subscription(Request,  "/api/arm/request",
                lambda m: print(format_request(m, "/api/arm/request")), qos_be)
            self.create_subscription(Response, "/api/arm/response",
                lambda m: print(format_response(m, "/api/arm/response")), qos_be)

            print(f"[{ts()}] Monitoring robot events... (click Stop to end)")
            print(f"[{ts()}] Watching: sport / motion_switcher / arm APIs")
            print(f"[{ts()}] Try pressing buttons on the controller or web app!")

    node = MonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()


if __name__ == "__main__":
    main()
