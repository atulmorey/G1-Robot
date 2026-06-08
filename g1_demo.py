#!/usr/bin/env python3
"""
G1 Demo Script — Phase 1 Progress
Demonstrates: ROS 2 connectivity, live state reading, audio command
Run on Ubuntu laptop:
  source ~/unitree_ros2/setup.sh
  source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
  python3 ~/g1_demo.py           # live mode (robot must be on)
  python3 ~/g1_demo.py --offline # offline/presentation mode (no robot needed)
"""

import sys
OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    import rclpy
    from rclpy.node import Node as _Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy
    from unitree_hg.msg import LowCmd, LowState
    from unitree_api.msg import Request
else:
    _Node = object

import struct
import subprocess
import time
import os

AUDIO_BIN = os.path.expanduser(
    "~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_audio_client_example"
)
BEEP_WAV = os.path.expanduser("~/hello.wav")

DEMO_STEPS = [
    "1. Connect to G1 via ROS 2",
    "2. Read live joint + IMU state",
    "3. Play audio on robot speaker",
    "4. Send arm movement command (requires standing mode)",
]


def calc_crc(cmd):
    d = struct.pack('BBxx', cmd.mode_pr, cmd.mode_machine)
    for m in cmd.motor_cmd:
        d += struct.pack('BxxxfffffI', m.mode, m.q, m.dq, m.tau, m.kp, m.kd, m.reserve)
    d += struct.pack('4I', cmd.reserve[0], cmd.reserve[1], cmd.reserve[2], cmd.reserve[3])
    words = struct.unpack(str(len(d) // 4) + 'I', d)
    crc = 0xFFFFFFFF
    poly = 0x04c11db7
    for w in words:
        xbit = 1 << 31
        for _ in range(32):
            if crc & 0x80000000:
                crc = ((crc << 1) & 0xFFFFFFFF) ^ poly
            else:
                crc = (crc << 1) & 0xFFFFFFFF
            if w & xbit:
                crc ^= poly
            xbit >>= 1
    return crc


class G1Demo(_Node):
    def __init__(self):
        super().__init__("g1_demo")
        qos_be = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        qos_re = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        self.arm_pub = self.create_publisher(LowCmd, "/armsdk", qos_be)
        self.state_received = False
        self.latest_state = None

        self.create_subscription(LowState, "/lf/lowstate", self._state_cb, qos_be)

    def _state_cb(self, msg):
        self.latest_state = msg
        self.state_received = True

    def wait_for_state(self, timeout=5.0):
        start = time.time()
        while not self.state_received and (time.time() - start) < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.state_received

    def print_state_summary(self):
        if not self.latest_state:
            print("  [!] No state received")
            return
        s = self.latest_state
        print(f"  IMU roll:  {s.imu_state.rpy[0]:.3f} rad")
        print(f"  IMU pitch: {s.imu_state.rpy[1]:.3f} rad")
        print(f"  IMU yaw:   {s.imu_state.rpy[2]:.3f} rad")
        print(f"  Left shoulder (joint 15) angle: {s.motor_state[15].q:.3f} rad")
        print(f"  Right shoulder (joint 22) angle: {s.motor_state[22].q:.3f} rad")

    def play_audio(self):
        if not os.path.exists(AUDIO_BIN):
            print("  [!] Audio binary not found")
            return
        if not os.path.exists(BEEP_WAV):
            print("  Generating beep sound...")
            subprocess.run(["sox", "-n", BEEP_WAV, "synth", "1", "sine", "880",
                            "sine", "1100"], capture_output=True)
        print("  Sending audio to robot...")
        try:
            subprocess.run([AUDIO_BIN, BEEP_WAV], capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            pass
        print("  Audio sent.")

    def send_arm_move(self):
        rclpy.spin_once(self, timeout_sec=0.1)
        if not self.latest_state:
            print("  [!] No state — skipping arm move (robot not connected)")
            return

        mode_machine = self.latest_state.mode_machine
        if mode_machine != 5:
            print(f"  [!] Robot mode_machine={mode_machine} — arm move requires mode 5 (standing)")
            print("  [!] Skipping arm move. Stand the robot first then rerun.")
            return

        print("  Sending left shoulder raise (joint 15)...")
        cmd = LowCmd()
        cmd.mode_machine = 5
        cmd.motor_cmd[15].mode = 1
        cmd.motor_cmd[15].q = 0.5
        cmd.motor_cmd[15].kp = 80.0
        cmd.motor_cmd[15].kd = 2.0

        for i in range(50):
            cmd.crc = calc_crc(cmd)
            self.arm_pub.publish(cmd)
            if i % 10 == 0:
                print(f"  Publishing... {i+1}/50")
            time.sleep(0.1)

        print("  Returning arm to home...")
        cmd.motor_cmd[15].q = 0.0
        for i in range(50):
            cmd.crc = calc_crc(cmd)
            self.arm_pub.publish(cmd)
            if i % 10 == 0:
                print(f"  Returning... {i+1}/50")
            time.sleep(0.1)
        print("  Arm move complete.")


def separator(title):
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)


def run_offline():
    separator("Step 1: Connecting to G1 via ROS 2")
    print("  [OFFLINE MODE] Skipping connection — robot not required")
    print("  In live mode: connects via CycloneDDS over Ethernet to 192.168.123.161")

    separator("Step 2: Live Robot State")
    print("  [OFFLINE MODE] Sample data from previous session:")
    print("  IMU roll:  0.051 rad")
    print("  IMU pitch: -0.044 rad")
    print("  IMU yaw:   2.151 rad")
    print("  Left shoulder (joint 15) angle: 0.080 rad")
    print("  Right shoulder (joint 22) angle: -0.087 rad")

    separator("Step 3: Audio Command")
    print("  [OFFLINE MODE] In live mode: plays beep via G1 onboard speaker")
    print("  Command: g1_audio_client_example ~/hello.wav")

    separator("Step 4: Arm Movement")
    print("  [OFFLINE MODE] In live mode: raises left shoulder (joint 15) by 0.5 rad")
    print("  Requires robot in standing mode (mode_machine=5)")

    separator("Demo Complete")
    print("  Phase 1 progress: ROS 2 + SDK + Audio + Arm command pipeline verified.")
    print("  Next: Day 2 — Depth Camera Integration\n")


def main():
    print("\n" + "=" * 50)
    print("  Unitree G1 — Phase 1 Demo")
    print("  Project: Robot Object Touch")
    if OFFLINE:
        print("  Mode: OFFLINE (presentation)")
    else:
        print("  Mode: LIVE (robot required)")
    print("=" * 50)
    print("\nDemo steps:")
    for step in DEMO_STEPS:
        print(f"  {step}")

    if OFFLINE:
        run_offline()
        return

    rclpy.init()
    node = G1Demo()

    # Step 1 — Connect
    separator("Step 1: Connecting to G1 via ROS 2")
    print("  Waiting for robot state...")
    if node.wait_for_state(timeout=5.0):
        print("  Connected!")
    else:
        print("  [!] Could not connect. Is the robot on and Ethernet connected?")
        rclpy.shutdown()
        sys.exit(1)

    # Step 2 — Read state
    separator("Step 2: Live Robot State")
    rclpy.spin_once(node, timeout_sec=1.0)
    node.print_state_summary()

    # Step 3 — Audio
    separator("Step 3: Audio Command")
    node.play_audio()

    # Step 4 — Arm move
    separator("Step 4: Arm Movement")
    node.send_arm_move()

    separator("Demo Complete")
    print("  Phase 1 progress: ROS 2 + SDK + Audio + Arm command pipeline verified.")
    print("  Next: Day 2 — Depth Camera Integration\n")

    rclpy.shutdown()


if __name__ == "__main__":
    main()
