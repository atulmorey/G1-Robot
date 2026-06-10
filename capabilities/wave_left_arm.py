#!/usr/bin/env python3
META = {
    "name": "Wave Left Arm",
    "icon": "👋",
    "description": "Robot waves left arm using sport gesture API.",
}

import sys
import time

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_api.msg import Request
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

ROBOT_SPORT_API_ID_HELLO = 1016


def main():
    if OFFLINE:
        print("OFFLINE: Wave left arm gesture simulated.")
        time.sleep(1)
        print("Done.")
        return

    rclpy.init()

    class WaveNode(Node):
        def __init__(self):
            super().__init__("wave_left_arm_node")
            qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            self.pub = self.create_publisher(Request, "/api/sport/request", qos)

        def send_wave(self):
            msg = Request()
            msg.header.identity.api_id = ROBOT_SPORT_API_ID_HELLO
            self.pub.publish(msg)
            print("Wave gesture sent via sport API.")

    node = WaveNode()
    time.sleep(0.5)
    print("Sending wave gesture...")
    node.send_wave()
    time.sleep(2.0)
    print("Done.")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
