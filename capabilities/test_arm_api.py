#!/usr/bin/env python3
META = {
    "name": "Test Arm API",
    "icon": "🧪",
    "description": "Tests arm task API with task_id 0,1,2,3 via loco client.",
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
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

LOCO_SET_ARM_TASK = 7106


def main():
    if OFFLINE:
        print("OFFLINE: Arm API test simulated.")
        return

    rclpy.init()

    class ArmTestNode(Node):
        def __init__(self):
            super().__init__("test_arm_api")
            qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            qos_be  = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.pub = self.create_publisher(Request, "/api/sport/request", qos_rel)
            self.response = None
            self.create_subscription(Response, "/api/sport/response",
                                     lambda m: setattr(self, 'response', m), qos_be)

        def send_arm_task(self, task_id):
            msg = Request()
            msg.header.identity.api_id = LOCO_SET_ARM_TASK
            msg.parameter = json.dumps({"data": task_id})
            self.response = None
            self.pub.publish(msg)
            start = time.time()
            while self.response is None and (time.time() - start) < 3.0:
                rclpy.spin_once(self, timeout_sec=0.1)
            if self.response:
                code = self.response.header.status.code
                print(f"  task_id={task_id} → response code={code} {'OK' if code==0 else 'FAIL'}")
            else:
                print(f"  task_id={task_id} → no response (timeout)")

    node = ArmTestNode()
    time.sleep(0.5)

    print("Testing arm task API (api_id=7106)...")
    print("Watch the robot arm carefully!")
    for task_id in [0, 1, 2, 3]:
        print(f">>> SENDING task_id={task_id} NOW <<<")
        node.send_arm_task(task_id)
        print(f"    task_id={task_id} sent — watching for 4 seconds...")
        time.sleep(4.0)
        print(f"    task_id={task_id} done.")

    print("Done — which task_id moved the arm?")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
