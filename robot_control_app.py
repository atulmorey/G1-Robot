#!/usr/bin/env python3
"""
Robot Control App — Executive Demo Launcher
Supports Unitree G1 (live + offline modes). Future: Boston Dynamics.
Run on Ubuntu laptop:
  source ~/unitree_ros2/setup.sh
  source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
  python3 ~/G1-Robot/robot_control_app.py
  python3 ~/G1-Robot/robot_control_app.py --offline   # no robot needed
"""

import sys
import os
import time
import struct
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node as _RosNode
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_hg.msg import LowCmd, LowState
        from unitree_api.msg import Request, Response
        import json
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

AUDIO_BIN = os.path.expanduser(
    "~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_audio_client_example"
)
BEEP_WAV = os.path.expanduser("~/hello.wav")

# ── Colors ────────────────────────────────────────────────────────────────────
BG          = "#1a1a2e"
PANEL_BG    = "#16213e"
ACCENT      = "#0f3460"
GREEN       = "#00d4aa"
RED         = "#e94560"
YELLOW      = "#f5a623"
WHITE       = "#e0e0e0"
GRAY        = "#6b7280"
BTN_BG      = "#0f3460"
BTN_ACTIVE  = "#1a5276"
BTN_HOVER   = "#1e4d8c"


# ── CRC helper ────────────────────────────────────────────────────────────────
def calc_crc(cmd):
    d = struct.pack('BBxx', cmd.mode_pr, cmd.mode_machine)
    for m in cmd.motor_cmd:
        d += struct.pack('BxxxfffffI', m.mode, m.q, m.dq, m.tau, m.kp, m.kd, m.reserve)
    d += struct.pack('4I', *cmd.reserve[:4])
    words = struct.unpack(str(len(d) // 4) + 'I', d)
    crc = 0xFFFFFFFF
    poly = 0x04c11db7
    for w in words:
        xbit = 1 << 31
        for _ in range(32):
            crc = (((crc << 1) & 0xFFFFFFFF) ^ poly) if (crc & 0x80000000) else ((crc << 1) & 0xFFFFFFFF)
            if w & xbit:
                crc ^= poly
            xbit >>= 1
    return crc


# ── ROS node (runs in background thread) ─────────────────────────────────────
class G1Node(_RosNode if ROS_AVAILABLE else object):
    def __init__(self):
        if ROS_AVAILABLE:
            super().__init__("robot_control_app")
        self.latest_state = None
        self.connected = False
        self._lock = threading.Lock()
        if ROS_AVAILABLE:
            qos_be  = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            qos_rel = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
            self.arm_pub = self.create_publisher(LowCmd, "/armsdk", qos_be)
            self.mode_pub = self.create_publisher(Request, "/api/motion_switcher/request", qos_rel)
            self.mode_response = None
            self.create_subscription(LowState, "/lf/lowstate", self._state_cb, qos_be)
            self.create_subscription(Response, "/api/motion_switcher/response", self._mode_cb, qos_be)

    def _state_cb(self, msg):
        with self._lock:
            self.latest_state = msg
            self.connected = True

    def _mode_cb(self, msg):
        self.mode_response = msg

    def get_state(self):
        with self._lock:
            return self.latest_state

    def send_arm_move(self, joint_idx, target_q, log_fn):
        if not ROS_AVAILABLE:
            log_fn("OFFLINE: arm move simulated")
            return
        state = self.get_state()
        if not state:
            log_fn("No robot state — cannot move arm")
            return
        if state.mode_machine != 5:
            log_fn(f"Robot not in standing mode (mode={state.mode_machine}). Stand first.")
            return
        log_fn(f"Moving joint {joint_idx} to {target_q:.2f} rad...")
        cmd = LowCmd()
        cmd.mode_machine = 5
        cmd.motor_cmd[joint_idx].mode = 1
        cmd.motor_cmd[joint_idx].q = target_q
        cmd.motor_cmd[joint_idx].kp = 80.0
        cmd.motor_cmd[joint_idx].kd = 2.0
        for i in range(50):
            cmd.crc = calc_crc(cmd)
            self.arm_pub.publish(cmd)
            time.sleep(0.05)
        log_fn("Returning arm to home...")
        cmd.motor_cmd[joint_idx].q = 0.0
        for i in range(50):
            cmd.crc = calc_crc(cmd)
            self.arm_pub.publish(cmd)
            time.sleep(0.05)
        log_fn("Arm move complete.")

    def play_audio(self, log_fn):
        if not ROS_AVAILABLE:
            log_fn("OFFLINE: audio simulated")
            return
        if not os.path.exists(AUDIO_BIN):
            log_fn("Audio binary not found")
            return
        if not os.path.exists(BEEP_WAV):
            log_fn("Generating beep...")
            subprocess.run(["sox", "-n", BEEP_WAV, "synth", "1", "sine", "880"], capture_output=True)
        log_fn("Sending audio to robot...")
        try:
            subprocess.run([AUDIO_BIN, BEEP_WAV], capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            pass
        log_fn("Audio sent.")

    def switch_mode(self, mode_name, log_fn):
        if not ROS_AVAILABLE:
            log_fn(f"OFFLINE: mode switch to '{mode_name}' simulated")
            return
        log_fn(f"Switching to mode: {mode_name}...")
        msg = Request()
        msg.header.identity.api_id = 1003  # RELEASE
        self.mode_response = None
        self.mode_pub.publish(msg)
        time.sleep(1)
        msg2 = Request()
        msg2.header.identity.api_id = 1002  # SELECT
        msg2.parameter = json.dumps({"name": mode_name})
        self.mode_pub.publish(msg2)
        start = time.time()
        while self.mode_response is None and (time.time() - start) < 5.0:
            rclpy.spin_once(self, timeout_sec=0.1)
        code = self.mode_response.header.status.code if self.mode_response else "timeout"
        log_fn(f"Mode switch response: {code}")


# ── Main App ──────────────────────────────────────────────────────────────────
class RobotControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Control — Executive Demo")
        self.root.configure(bg=BG)
        self.root.geometry("900x680")
        self.root.minsize(800, 600)

        self.robot_var = tk.StringVar(value="Unitree G1")
        self.node = None
        self.ros_thread = None
        self._build_ui()
        self._start_ros()
        self._poll_status()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=ACCENT, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="ROBOT CONTROL", font=("Helvetica", 20, "bold"),
                 bg=ACCENT, fg=WHITE).pack(side=tk.LEFT, padx=20)
        tk.Label(hdr, text="Executive Demo", font=("Helvetica", 11),
                 bg=ACCENT, fg=GRAY).pack(side=tk.LEFT)

        mode_lbl = "OFFLINE MODE" if OFFLINE else "LIVE MODE"
        mode_col = YELLOW if OFFLINE else GREEN
        tk.Label(hdr, text=mode_lbl, font=("Helvetica", 10, "bold"),
                 bg=ACCENT, fg=mode_col).pack(side=tk.RIGHT, padx=20)

        # Robot selector
        sel_frame = tk.Frame(self.root, bg=BG, pady=8)
        sel_frame.pack(fill=tk.X, padx=20)
        tk.Label(sel_frame, text="Robot:", font=("Helvetica", 11),
                 bg=BG, fg=WHITE).pack(side=tk.LEFT)
        robots = ["Unitree G1", "Boston Dynamics (coming soon)"]
        for r in robots:
            state = tk.NORMAL if r == "Unitree G1" else tk.DISABLED
            rb = tk.Radiobutton(sel_frame, text=r, variable=self.robot_var,
                                value=r, font=("Helvetica", 11),
                                bg=BG, fg=WHITE, selectcolor=ACCENT,
                                activebackground=BG, activeforeground=WHITE,
                                state=state, command=self._on_robot_change)
            rb.pack(side=tk.LEFT, padx=12)

        # Main area: health panel + action buttons
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=4)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        self._build_health_panel(main)
        self._build_action_panel(main)

        # Log
        self._build_log(self.root)

    def _build_health_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL_BG, bd=0, relief=tk.FLAT)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(frame, text="HEALTH STATUS", font=("Helvetica", 12, "bold"),
                 bg=PANEL_BG, fg=WHITE).pack(pady=(14, 6))

        self.conn_dot   = self._status_row(frame, "Connection")
        self.batt_dot   = self._status_row(frame, "Battery")
        self.imu_dot    = self._status_row(frame, "IMU")
        self.motors_dot = self._status_row(frame, "Motors")

        tk.Label(frame, text="IMU", font=("Helvetica", 10, "bold"),
                 bg=PANEL_BG, fg=GRAY).pack(pady=(10, 0))
        self.roll_val  = self._imu_row(frame, "Roll")
        self.pitch_val = self._imu_row(frame, "Pitch")
        self.yaw_val   = self._imu_row(frame, "Yaw")

        tk.Label(frame, text="Joints", font=("Helvetica", 10, "bold"),
                 bg=PANEL_BG, fg=GRAY).pack(pady=(10, 0))
        self.lshoulder_val = self._imu_row(frame, "L Shoulder (15)")
        self.rshoulder_val = self._imu_row(frame, "R Shoulder (22)")

        self._make_btn(frame, "Refresh Health", self._refresh_health,
                       bg=ACCENT, pady=12).pack(fill=tk.X, padx=14, pady=(16, 14))

    def _status_row(self, parent, label):
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(fill=tk.X, padx=14, pady=3)
        dot = tk.Label(row, text="●", font=("Helvetica", 14), bg=PANEL_BG, fg=GRAY)
        dot.pack(side=tk.LEFT)
        tk.Label(row, text=label, font=("Helvetica", 11),
                 bg=PANEL_BG, fg=WHITE).pack(side=tk.LEFT, padx=6)
        val = tk.Label(row, text="—", font=("Helvetica", 10),
                       bg=PANEL_BG, fg=GRAY)
        val.pack(side=tk.RIGHT)
        dot._val_label = val
        return dot

    def _imu_row(self, parent, label):
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(fill=tk.X, padx=20, pady=1)
        tk.Label(row, text=label, font=("Helvetica", 10),
                 bg=PANEL_BG, fg=GRAY).pack(side=tk.LEFT)
        val = tk.Label(row, text="—", font=("Helvetica", 10, "bold"),
                       bg=PANEL_BG, fg=WHITE)
        val.pack(side=tk.RIGHT)
        return val

    def _build_action_panel(self, parent):
        frame = tk.Frame(parent, bg=PANEL_BG)
        frame.grid(row=0, column=1, sticky="nsew")

        tk.Label(frame, text="ACTIONS", font=("Helvetica", 12, "bold"),
                 bg=PANEL_BG, fg=WHITE).pack(pady=(14, 6))

        grid = tk.Frame(frame, bg=PANEL_BG)
        grid.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        buttons = [
            ("Stand Up",        "⬆",  self._cmd_stand,     GREEN),
            ("Sit Down",        "⬇",  self._cmd_sit,       YELLOW),
            ("Wave Left Arm",   "✋",  self._cmd_wave_left, BTN_BG),
            ("Wave Right Arm",  "🤚",  self._cmd_wave_right, BTN_BG),
            ("Play Audio",      "🔊",  self._cmd_audio,     BTN_BG),
            ("Walk Forward",    "▶",  self._cmd_walk,      BTN_BG),
        ]

        for i, (label, icon, cmd, color) in enumerate(buttons):
            r, c = divmod(i, 2)
            btn = self._big_btn(grid, icon, label, cmd, color)
            btn.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            grid.rowconfigure(r, weight=1)

    def _big_btn(self, parent, icon, label, command, bg=BTN_BG):
        f = tk.Frame(parent, bg=bg, cursor="hand2")
        f.bind("<Button-1>", lambda e: command())
        f.bind("<Enter>", lambda e: f.configure(bg=BTN_HOVER))
        f.bind("<Leave>", lambda e: f.configure(bg=bg))

        icon_lbl = tk.Label(f, text=icon, font=("Helvetica", 22),
                            bg=bg, fg=WHITE, cursor="hand2")
        icon_lbl.pack(pady=(14, 2))
        icon_lbl.bind("<Button-1>", lambda e: command())
        icon_lbl.bind("<Enter>", lambda e: [f.configure(bg=BTN_HOVER), icon_lbl.configure(bg=BTN_HOVER)])
        icon_lbl.bind("<Leave>", lambda e: [f.configure(bg=bg), icon_lbl.configure(bg=bg)])

        txt_lbl = tk.Label(f, text=label, font=("Helvetica", 11, "bold"),
                           bg=bg, fg=WHITE, cursor="hand2")
        txt_lbl.pack(pady=(0, 14))
        txt_lbl.bind("<Button-1>", lambda e: command())
        txt_lbl.bind("<Enter>", lambda e: [f.configure(bg=BTN_HOVER), txt_lbl.configure(bg=BTN_HOVER)])
        txt_lbl.bind("<Leave>", lambda e: [f.configure(bg=bg), txt_lbl.configure(bg=bg)])

        return f

    def _make_btn(self, parent, text, command, bg=BTN_BG, pady=8):
        btn = tk.Button(parent, text=text, command=command,
                        font=("Helvetica", 11, "bold"),
                        bg=bg, fg=WHITE, activebackground=BTN_ACTIVE,
                        activeforeground=WHITE, relief=tk.FLAT,
                        pady=pady, cursor="hand2", bd=0)
        return btn

    def _build_log(self, parent):
        log_frame = tk.Frame(parent, bg=PANEL_BG)
        log_frame.pack(fill=tk.X, padx=20, pady=(0, 14))

        header = tk.Frame(log_frame, bg=PANEL_BG)
        header.pack(fill=tk.X)
        tk.Label(header, text="LOG", font=("Helvetica", 10, "bold"),
                 bg=PANEL_BG, fg=GRAY).pack(side=tk.LEFT, padx=10, pady=4)
        self._make_btn(header, "Clear", self._clear_log, bg=ACCENT, pady=2).pack(
            side=tk.RIGHT, padx=8, pady=4)

        self.log_text = tk.Text(log_frame, height=5, bg="#0d1117", fg=GREEN,
                                font=("Courier", 10), relief=tk.FLAT,
                                state=tk.DISABLED, wrap=tk.WORD, bd=0)
        self.log_text.pack(fill=tk.X, padx=8, pady=(0, 8))

    # ── ROS background thread ─────────────────────────────────────────────────
    def _start_ros(self):
        if not ROS_AVAILABLE:
            self._log("Running in OFFLINE mode — no ROS connection")
            return
        try:
            rclpy.init()
            self.node = G1Node()
            self.ros_thread = threading.Thread(target=self._ros_spin, daemon=True)
            self.ros_thread.start()
            self._log("ROS 2 initialized — waiting for robot...")
        except Exception as e:
            self._log(f"ROS init error: {e}")

    def _ros_spin(self):
        while rclpy.ok():
            try:
                rclpy.spin_once(self.node, timeout_sec=0.1)
            except Exception:
                break

    # ── Polling & status update ───────────────────────────────────────────────
    def _poll_status(self):
        self._update_health_display()
        self.root.after(2000, self._poll_status)

    def _update_health_display(self):
        if OFFLINE:
            self._set_dot(self.conn_dot, "yellow", "OFFLINE")
            self._set_dot(self.batt_dot, "yellow", "—")
            self._set_dot(self.imu_dot, "yellow", "—")
            self._set_dot(self.motors_dot, "yellow", "—")
            self.roll_val.config(text="0.051 rad")
            self.pitch_val.config(text="-0.044 rad")
            self.yaw_val.config(text="2.151 rad")
            self.lshoulder_val.config(text="0.080 rad")
            self.rshoulder_val.config(text="-0.087 rad")
            return

        state = self.node.get_state() if self.node else None
        if state:
            self._set_dot(self.conn_dot, "green", "OK")
            self._set_dot(self.imu_dot, "green", "OK")
            self._set_dot(self.motors_dot, "green", "OK")
            # Battery: G1 doesn't publish battery in LowState via this topic
            self._set_dot(self.batt_dot, "yellow", "N/A")
            s = state
            self.roll_val.config(text=f"{s.imu_state.rpy[0]:.3f} rad")
            self.pitch_val.config(text=f"{s.imu_state.rpy[1]:.3f} rad")
            self.yaw_val.config(text=f"{s.imu_state.rpy[2]:.3f} rad")
            self.lshoulder_val.config(text=f"{s.motor_state[15].q:.3f} rad")
            self.rshoulder_val.config(text=f"{s.motor_state[22].q:.3f} rad")
        else:
            self._set_dot(self.conn_dot, "red", "NO SIGNAL")
            self._set_dot(self.batt_dot, "gray", "—")
            self._set_dot(self.imu_dot, "red", "—")
            self._set_dot(self.motors_dot, "red", "—")
            self.roll_val.config(text="—")
            self.pitch_val.config(text="—")
            self.yaw_val.config(text="—")
            self.lshoulder_val.config(text="—")
            self.rshoulder_val.config(text="—")

    def _set_dot(self, dot_label, color, val_text=""):
        colors = {"green": GREEN, "red": RED, "yellow": YELLOW, "gray": GRAY}
        dot_label.config(fg=colors.get(color, GRAY))
        dot_label._val_label.config(text=val_text)

    # ── Commands ──────────────────────────────────────────────────────────────
    def _run_in_thread(self, fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    def _cmd_stand(self):
        self._log("Stand Up: switching to normal mode...")
        self._run_in_thread(
            lambda: self.node.switch_mode("normal", self._log) if self.node
            else self._log("OFFLINE: stand simulated"))

    def _cmd_sit(self):
        self._log("Sit Down: switching to ai mode...")
        self._run_in_thread(
            lambda: self.node.switch_mode("ai", self._log) if self.node
            else self._log("OFFLINE: sit simulated"))

    def _cmd_wave_left(self):
        self._log("Wave Left Arm (joint 15)...")
        self._run_in_thread(
            lambda: self.node.send_arm_move(15, 0.8, self._log) if self.node
            else self._log("OFFLINE: wave left simulated"))

    def _cmd_wave_right(self):
        self._log("Wave Right Arm (joint 22)...")
        self._run_in_thread(
            lambda: self.node.send_arm_move(22, -0.8, self._log) if self.node
            else self._log("OFFLINE: wave right simulated"))

    def _cmd_audio(self):
        self._log("Play Audio...")
        self._run_in_thread(
            lambda: self.node.play_audio(self._log) if self.node
            else self._log("OFFLINE: audio simulated"))

    def _cmd_walk(self):
        self._log("Walk Forward: not yet implemented (Phase 2)")

    def _refresh_health(self):
        self._log("Refreshing health status...")
        self._update_health_display()

    def _on_robot_change(self):
        self._log(f"Robot: {self.robot_var.get()}")

    # ── Log helpers ───────────────────────────────────────────────────────────
    def _log(self, msg):
        def _do():
            self.log_text.config(state=tk.NORMAL)
            ts = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _do)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = RobotControlApp(root)

    def _on_close():
        try:
            if ROS_AVAILABLE and rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
