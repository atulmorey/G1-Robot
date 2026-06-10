#!/usr/bin/env python3
META = {"name": "Arm Task 2", "icon": "2️⃣", "description": "Send arm task_id=2 and log joint positions before/after"}
import sys, time, json
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
        ROS_AVAILABLE = False; OFFLINE = True
else:
    ROS_AVAILABLE = False

def main():
    if OFFLINE:
        print("OFFLINE: arm task_id=2 simulated"); return
    rclpy.init()
    class N(Node):
        def __init__(self):
            super().__init__("arm_task_node")
            qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            qos_be  = QoSProfile(depth=1,  reliability=ReliabilityPolicy.BEST_EFFORT)
            self.pub = self.create_publisher(Request, "/api/sport/request", qos_rel)
            self.resp = None
            self.state = None
            self.create_subscription(Response, "/api/sport/response",
                lambda m: setattr(self, 'resp', m), qos_be)
            self.create_subscription(LowState, "/lf/lowstate",
                lambda m: setattr(self, 'state', m), qos_be)

        def joints(self):
            if not self.state: return "no state"
            s = self.state
            return (f"L_shoulder={s.motor_state[15].q:.3f} "
                    f"L_roll={s.motor_state[16].q:.3f} "
                    f"L_yaw={s.motor_state[17].q:.3f} "
                    f"L_elbow={s.motor_state[18].q:.3f} "
                    f"R_shoulder={s.motor_state[22].q:.3f}")

    node = N()
    time.sleep(1.0)
    rclpy.spin_once(node, timeout_sec=1.0)
    print(f"Before: {node.joints()}")

    print("Sending arm task_id=2...")
    msg = Request()
    msg.header.identity.api_id = 7106
    msg.parameter = json.dumps({"data": 2})
    node.pub.publish(msg)
    start = time.time()
    while node.resp is None and (time.time()-start)<3: rclpy.spin_once(node, timeout_sec=0.1)
    code = node.resp.header.status.code if node.resp else "timeout"
    print(f"Response: {code}")

    for i in range(5):
        time.sleep(0.5)
        rclpy.spin_once(node, timeout_sec=0.1)
        print(f"t+{(i+1)*0.5:.1f}s: {node.joints()}")

    print("Done.")
    rclpy.shutdown()

if __name__ == "__main__": main()
