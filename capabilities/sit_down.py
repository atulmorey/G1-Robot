#!/usr/bin/env python3
META = {
    "name": "Sit Down",
    "icon": "⬇",
    "description": "Switch robot to AI (sit/rest) mode.",
}

import sys
import time

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_api.msg import Request, Response
        import json
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

SELECT_MODE  = 1002
RELEASE_MODE = 1003


def main():
    if OFFLINE:
        print("OFFLINE: Releasing current mode...")
        time.sleep(0.5)
        print("OFFLINE: Selecting AI (sit) mode...")
        time.sleep(0.5)
        print("Done.")
        return

    rclpy.init()

    class Switcher(Node):
        def __init__(self):
            super().__init__("sit_down_node")
            qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            qos_be  = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.pub = self.create_publisher(Request, "/api/motion_switcher/request", qos_rel)
            self.response = None
            self.create_subscription(Response, "/api/motion_switcher/response", self._cb, qos_be)

        def _cb(self, msg):
            self.response = msg

        def send(self, api_id, param=None, timeout=5.0):
            msg = Request()
            msg.header.identity.api_id = api_id
            if param:
                msg.parameter = json.dumps(param)
            self.response = None
            self.pub.publish(msg)
            start = time.time()
            while self.response is None and (time.time() - start) < timeout:
                rclpy.spin_once(self, timeout_sec=0.1)
            return self.response

    node = Switcher()
    time.sleep(0.5)

    print("Releasing current mode...")
    node.send(RELEASE_MODE)
    time.sleep(1)

    print("Selecting AI (sit) mode...")
    resp = node.send(SELECT_MODE, {"name": "ai"})
    code = resp.header.status.code if resp else "timeout"
    print(f"Response: {code}")

    rclpy.shutdown()


if __name__ == "__main__":
    main()
