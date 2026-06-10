#!/usr/bin/env python3
META = {"name": "Arm Task 1", "icon": "1️⃣", "description": "Send arm task_id=1"}
import sys, time, json
OFFLINE = "--offline" in sys.argv
if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_api.msg import Request, Response
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False; OFFLINE = True
else:
    ROS_AVAILABLE = False

def main():
    if OFFLINE:
        print("OFFLINE: arm task_id=1 simulated"); return
    rclpy.init()
    class N(Node):
        def __init__(self):
            super().__init__("arm_task_node")
            qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            self.pub = self.create_publisher(Request, "/api/sport/request", qos)
            self.resp = None
            self.create_subscription(Response, "/api/sport/response",
                lambda m: setattr(self, 'resp', m),
                QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT))
    node = N()
    time.sleep(0.5)
    print("Sending arm task_id=1...")
    msg = Request()
    msg.header.identity.api_id = 7106
    msg.parameter = json.dumps({"data": 1})
    node.pub.publish(msg)
    start = time.time()
    while node.resp is None and (time.time()-start)<3: rclpy.spin_once(node, timeout_sec=0.1)
    code = node.resp.header.status.code if node.resp else "timeout"
    print(f"Response: {code} {'OK' if code==0 else 'FAIL/timeout'}")
    print("Watch the arm for 3 seconds...")
    time.sleep(3)
    print("Done.")
    rclpy.shutdown()

if __name__ == "__main__": main()
