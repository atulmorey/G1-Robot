#!/usr/bin/env python3
"""
G1 Motion Mode Switcher
Releases ai mode and switches to normal (sport_mode)
Run: python3 ~/G1-Robot/g1_switch_sport.py
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from unitree_api.msg import Request, Response
import json
import time

CHECK_MODE   = 1001
SELECT_MODE  = 1002
RELEASE_MODE = 1003

class MotionSwitcher(Node):
    def __init__(self):
        super().__init__("motion_switcher")
        qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        qos_be  = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.pub = self.create_publisher(Request, "/api/motion_switcher/request", qos_rel)
        self.response = None
        self.create_subscription(Response, "/api/motion_switcher/response", self._cb, qos_be)

    def _cb(self, msg):
        self.response = msg

    def send_and_wait(self, api_id, param=None, timeout=5.0):
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

    def check_mode(self):
        resp = self.send_and_wait(CHECK_MODE)
        if resp:
            print(f"  Current mode: {resp.data}")
        else:
            print("  No response")

    def release_mode(self):
        print("Releasing current mode...")
        resp = self.send_and_wait(RELEASE_MODE)
        if resp:
            print(f"  Release response code: {resp.header.status.code}")
        else:
            print("  No response")

    def select_mode(self, name):
        print(f"Selecting mode: {name}...")
        resp = self.send_and_wait(SELECT_MODE, {"name": name})
        if resp:
            print(f"  Select response code: {resp.header.status.code}")
        else:
            print("  No response")

def main():
    rclpy.init()
    node = MotionSwitcher()
    time.sleep(1)

    print("=== Step 1: Check current mode ===")
    node.check_mode()
    time.sleep(1)

    print("=== Step 2: Release current mode ===")
    node.release_mode()
    time.sleep(2)

    print("=== Step 3: Select normal mode ===")
    node.select_mode("normal")
    time.sleep(2)

    print("=== Step 4: Verify mode ===")
    node.check_mode()

    rclpy.shutdown()

if __name__ == "__main__":
    main()
