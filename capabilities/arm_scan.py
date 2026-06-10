#!/usr/bin/env python3
META = {
    "name": "Arm Scan Tasks",
    "icon": "🔍",
    "description": "Tests arm task IDs 10-20 to find forward reach positions.",
}

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
        print("OFFLINE: arm scan simulated"); return

    rclpy.init()
    class N(Node):
        def __init__(self):
            super().__init__("arm_scan")
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
            return (f"Lp={s.motor_state[15].q:.2f} "
                    f"Lr={s.motor_state[16].q:.2f} "
                    f"Le={s.motor_state[18].q:.2f} "
                    f"Rp={s.motor_state[22].q:.2f}")

        def send(self, task_id):
            msg = Request()
            msg.header.identity.api_id = 7106
            msg.parameter = json.dumps({"data": task_id})
            self.resp = None
            self.pub.publish(msg)
            start = time.time()
            while self.resp is None and (time.time()-start)<2:
                rclpy.spin_once(self, timeout_sec=0.1)
            return self.resp.header.status.code if self.resp else "timeout"

    node = N()
    time.sleep(1)

    print("Scanning task IDs 10-20 — watch arm for each!")
    for task_id in range(10, 21):
        rclpy.spin_once(node, timeout_sec=0.2)
        before = node.joints()
        code = node.send(task_id)
        time.sleep(1.5)
        rclpy.spin_once(node, timeout_sec=0.2)
        after = node.joints()
        moved = before != after
        print(f"task={task_id:2d} code={code} moved={'YES***' if moved else 'no'} | {after}")

    print("Done — note which task IDs show YES and what the arm did.")
    rclpy.shutdown()

if __name__ == "__main__": main()
