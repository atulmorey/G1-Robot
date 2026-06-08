#!/usr/bin/env python3
"""
Activate G1 sport mode via motion switcher
Run: python3 ~/G1-Robot/g1_switch_sport.py
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from unitree_api.msg import Request
import json
import time

class SportModeSwitcher(Node):
    def __init__(self):
        super().__init__("sport_mode_switcher")
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self.pub = self.create_publisher(Request, "/api/motion_switcher/request", qos)
        self.get_logger().info("SportModeSwitcher ready")

    def switch_to_sport(self):
        msg = Request()
        msg.header.identity.api_id = 1001
        msg.parameter = json.dumps({"name": "sport_mode"})
        time.sleep(1)
        print("Sending switch to sport mode...")
        self.pub.publish(msg)
        time.sleep(2)
        print("Done. Check if /api/sport/response now has Publisher count: 1")

def main():
    rclpy.init()
    node = SportModeSwitcher()
    node.switch_to_sport()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
