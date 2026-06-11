META = {
    "name": "Joint Map",
    "icon": "🗺",
    "description": "Shows all 29 joint positions, velocities, torques and full IMU state."
}

import math
import argparse
import sys

JOINT_NAMES = [
    "L_hip_pitch", "L_hip_roll", "L_hip_yaw", "L_knee", "L_ankle_pitch", "L_ankle_roll",
    "R_hip_pitch", "R_hip_roll", "R_hip_yaw", "R_knee", "R_ankle_pitch", "R_ankle_roll",
    "waist_yaw", "waist_roll", "waist_pitch",
    "L_shoulder_pitch", "L_shoulder_roll", "L_shoulder_yaw", "L_elbow",
    "L_wrist_roll", "L_wrist_pitch", "L_wrist_yaw",
    "R_shoulder_pitch", "R_shoulder_roll", "R_shoulder_yaw", "R_elbow",
    "R_wrist_roll", "R_wrist_pitch", "R_wrist_yaw",
]

MODE_NAMES = {
    0: "IDLE",
    1: "DAMPING",
    2: "LOCK",
    3: "STAND",
    4: "WALK",
    5: "STAIRS",
    11: "FREE",
}


def print_table(motor_states, imu, mode_machine):
    header = f"{'IDX':>4} | {'NAME':<22} | {'q (rad)':>9} | {'q (deg)':>9} | {'dq (rad/s)':>11} | {'tau_est (Nm)':>13}"
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for i, name in enumerate(JOINT_NAMES):
        ms = motor_states[i]
        q = getattr(ms, 'q', 0.0)
        dq = getattr(ms, 'dq', 0.0)
        tau = getattr(ms, 'tau_est', 0.0)
        q_deg = math.degrees(q)
        print(f"{i:>4} | {name:<22} | {q:>9.4f} | {q_deg:>9.3f} | {dq:>11.4f} | {tau:>13.4f}")
    print(sep)

    # IMU section
    rpy = getattr(imu, 'rpy', None)
    acc = getattr(imu, 'accelerometer', None)
    gyro = getattr(imu, 'gyroscope', None)

    def get_xyz(obj):
        if obj is None:
            return 0.0, 0.0, 0.0
        if hasattr(obj, '__getitem__'):
            try:
                return float(obj[0]), float(obj[1]), float(obj[2])
            except Exception:
                pass
        return getattr(obj, 'x', 0.0), getattr(obj, 'y', 0.0), getattr(obj, 'z', 0.0)

    if rpy is not None:
        if hasattr(rpy, '__getitem__'):
            try:
                roll, pitch, yaw = float(rpy[0]), float(rpy[1]), float(rpy[2])
            except Exception:
                roll = getattr(rpy, 'x', 0.0)
                pitch = getattr(rpy, 'y', 0.0)
                yaw = getattr(rpy, 'z', 0.0)
        else:
            roll = getattr(rpy, 'x', 0.0)
            pitch = getattr(rpy, 'y', 0.0)
            yaw = getattr(rpy, 'z', 0.0)
    else:
        roll, pitch, yaw = 0.0, 0.0, 0.0

    ax, ay, az = get_xyz(acc)
    gx, gy, gz = get_xyz(gyro)

    print()
    print("IMU State:")
    print(f"  RPY:  roll={roll:.4f}  pitch={pitch:.4f}  yaw={yaw:.4f} (rad)")
    print(f"  ACC:  x={ax:.4f}  y={ay:.4f}  z={az:.4f} (m/s^2)")
    print(f"  GYRO: x={gx:.4f}  y={gy:.4f}  z={gz:.4f} (rad/s)")
    print()

    mode_name = MODE_NAMES.get(int(mode_machine), "UNKNOWN")
    print(f"  mode_machine: {int(mode_machine)} ({mode_name})")
    print(sep)


def run_offline():
    print("OFFLINE MODE - simulated data")
    print()

    class FakeMotorState:
        q = 0.0
        dq = 0.0
        tau_est = 0.0

    class FakeRPY:
        x = 0.0
        y = 0.0
        z = 0.0

    class FakeAcc:
        x = 0.0
        y = 0.0
        z = 0.0

    class FakeGyro:
        x = 0.0
        y = 0.0
        z = 0.0

    class FakeIMU:
        rpy = FakeRPY()
        accelerometer = FakeAcc()
        gyroscope = FakeGyro()

    motor_states = [FakeMotorState() for _ in range(29)]
    imu = FakeIMU()
    print_table(motor_states, imu, 0)


def run_live():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
    from unitree_go.msg import LowState

    class JointMapNode(Node):
        def __init__(self):
            super().__init__('joint_map_node')
            self.msg = None
            qos = QoSProfile(
                reliability=ReliabilityPolicy.BEST_EFFORT,
                durability=DurabilityPolicy.VOLATILE,
                history=HistoryPolicy.KEEP_LAST,
                depth=1,
            )
            self.sub = self.create_subscription(
                LowState,
                '/lf/lowstate',
                self._cb,
                qos,
            )

        def _cb(self, msg):
            self.msg = msg

    rclpy.init()
    node = JointMapNode()

    import time
    deadline = time.time() + 8.0
    while time.time() < deadline and node.msg is None:
        rclpy.spin_once(node, timeout_sec=0.1)

    if node.msg is None:
        node.destroy_node()
        rclpy.shutdown()
        print("ERROR: No LowState message received on /lf/lowstate within 8 seconds.", file=sys.stderr)
        sys.exit(1)

    msg = node.msg
    motor_states = msg.motor_state[:29]
    imu = msg.imu_state
    mode_machine = getattr(msg, 'mode_machine', 0)

    node.destroy_node()
    rclpy.shutdown()

    print_table(motor_states, imu, mode_machine)


def main():
    parser = argparse.ArgumentParser(description=META["description"])
    parser.add_argument('--offline', action='store_true', help='Print sample table with simulated zero data')
    args = parser.parse_args()

    if args.offline:
        run_offline()
    else:
        run_live()


if __name__ == '__main__':
    main()
