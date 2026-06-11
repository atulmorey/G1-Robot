#!/usr/bin/env python3
"""
Robot Control Web Server
Run: python3 ~/G1-Robot/server.py [--offline]
Then open: http://localhost:5000
"""

import sys
import os
import ast
import uuid
import time
import math
import json as _json
import datetime
import threading
import subprocess
from collections import deque
from flask import Flask, render_template, request, jsonify, Response

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node as _RosNode
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from unitree_hg.msg import LowState
        from unitree_go.msg import SportModeState
        from std_msgs.msg import String as RosString
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

CAPABILITIES_DIR = os.path.join(os.path.dirname(__file__), "capabilities")

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

JOINT_NAMES = [
    "L_hip_pitch", "L_hip_roll", "L_hip_yaw", "L_knee", "L_ankle_pitch", "L_ankle_roll",
    "R_hip_pitch", "R_hip_roll", "R_hip_yaw", "R_knee", "R_ankle_pitch", "R_ankle_roll",
    "waist_yaw", "waist_roll", "waist_pitch",
    "L_shoulder_pitch", "L_shoulder_roll", "L_shoulder_yaw", "L_elbow", "L_wrist_roll", "L_wrist_pitch", "L_wrist_yaw",
    "R_shoulder_pitch", "R_shoulder_roll", "R_shoulder_yaw", "R_elbow", "R_wrist_roll", "R_wrist_pitch", "R_wrist_yaw",
]


# ── Health Monitor ─────────────────────────────────────────────────────────────
class HealthMonitor(_RosNode if ROS_AVAILABLE else object):
    def __init__(self):
        if ROS_AVAILABLE:
            super().__init__("robot_control_server")
        self._lock = threading.Lock()
        self._last_msg_time = 0.0
        self._state = {
            "connected": False,
            "offline_mode": OFFLINE,
            "imu": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
            "joints": {"left_shoulder": 0.0, "right_shoulder": 0.0},
            "last_update": 0.0,
        }
        self._sport_mode = "—"
        self._gait = "—"
        self._arm_action = {"holding": False, "id": 0, "name": ""}
        self._recording = False
        self._record_buffer = []
        self._record_start_time = 0.0
        self._record_counter = 0
        self._state_cb_count = 0  # diagnostic: total callbacks since start

        if ROS_AVAILABLE:
            qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.create_subscription(LowState, "/lf/lowstate", self._state_cb, qos)
            self.create_subscription(SportModeState, "/lf/sportmodestate",
                                     self._sport_cb, qos)
            self.create_subscription(RosString, "/arm/action/state",
                                     self._arm_action_cb, qos)

    SPORT_MODES = {
        0: "IDLE", 1: "BALANCE_STAND", 2: "POSE", 3: "LOCOMOTION",
        5: "LIE_DOWN", 6: "JOINT_LOCK", 7: "DAMPING", 8: "RECOVERY_STAND",
        10: "SIT", 11: "FRONT_FLIP"
    }
    GAIT_TYPES = {
        0: "idle", 1: "trot", 2: "run", 3: "climb", 4: "down_stair", 9: "adjust"
    }
    MODE_NAMES = {
        0: "IDLE", 1: "BALANCE_STAND", 2: "POSE", 3: "LOCOMOTION",
        5: "JOINT_LOCK", 6: "DAMPING", 7: "RECOVERY_STAND", 9: "SIT"
    }

    def _sport_cb(self, msg):
        self._sport_mode = self.SPORT_MODES.get(int(msg.mode), f"mode_{msg.mode}")
        self._gait = self.GAIT_TYPES.get(int(msg.gait_type), f"gait_{msg.gait_type}")

    def _arm_action_cb(self, msg):
        try:
            self._arm_action = _json.loads(msg.data)
        except Exception:
            pass

    def _state_cb(self, msg):
        now = time.time()
        mode = int(msg.mode_machine)
        with self._lock:
            self._last_msg_time = now
            self._state = {
                "connected": True,
                "offline_mode": False,
                "mode": self._sport_mode,
                "mode_id": mode,
                "gait": self._gait,
                "imu": {
                    "roll":  round(float(msg.imu_state.rpy[0]), 3),
                    "pitch": round(float(msg.imu_state.rpy[1]), 3),
                    "yaw":   round(float(msg.imu_state.rpy[2]), 3),
                },
                "joints": {
                    "left_shoulder":  round(float(msg.motor_state[15].q), 3),
                    "right_shoulder": round(float(msg.motor_state[22].q), 3),
                },
                "arm_action": dict(self._arm_action),
                "last_update": now,
            }
            self._state_cb_count += 1
            if self._recording:
                self._record_counter += 1
                n = min(29, len(msg.motor_state))
                self._record_buffer.append({
                    "t": round(now - self._record_start_time, 4),
                    "mode": mode,
                    "sport": self._sport_mode,
                    "gesture": dict(self._arm_action),
                    "imu": {
                        "rpy":  [round(float(msg.imu_state.rpy[i]),  4) for i in range(3)],
                        "acc":  [round(float(msg.imu_state.acc[i]),  4) for i in range(3)],
                        "gyro": [round(float(msg.imu_state.gyro[i]), 4) for i in range(3)],
                    },
                    "joints": [
                        [round(float(msg.motor_state[i].q),  4),
                         round(float(msg.motor_state[i].dq), 4),
                         round(float(getattr(msg.motor_state[i], "tau_est", 0.0)), 4)]
                        for i in range(n)
                    ],
                })

    def start_recording(self):
        with self._lock:
            self._record_buffer = []
            self._recording = True
            self._record_start_time = time.time()
            self._record_counter = 0

    def stop_recording(self):
        with self._lock:
            self._recording = False
            samples = list(self._record_buffer)
            self._record_buffer = []
        return samples

    def is_recording(self):
        with self._lock:
            return self._recording

    def recording_stats(self):
        with self._lock:
            return {
                "recording": self._recording,
                "buffered": len(self._record_buffer),
                "cb_count": self._state_cb_count,
                "gesture": dict(self._arm_action),
            }

    def to_dict(self):
        if OFFLINE:
            return {
                "connected": False, "offline_mode": True, "mode": "OFFLINE", "mode_id": -1,
                "imu": {"roll": 0.051, "pitch": -0.044, "yaw": 2.151},
                "joints": {"left_shoulder": 0.080, "right_shoulder": -0.087},
                "last_update": time.time(),
            }
        with self._lock:
            if self._last_msg_time and (time.time() - self._last_msg_time) > 3.0:
                self._state["connected"] = False
            return dict(self._state)

    def spin(self):
        while ROS_AVAILABLE and rclpy.ok():
            try:
                rclpy.spin_once(self, timeout_sec=0.05)
            except Exception:
                break

    def start(self):
        if ROS_AVAILABLE:
            threading.Thread(target=self.spin, daemon=True).start()


# ── Process Manager ────────────────────────────────────────────────────────────
class ProcessManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None
        self._run_id = None
        self._output = deque(maxlen=500)

    def run(self, script_name):
        safe = all(c.isalnum() or c == "_" for c in script_name)
        if not safe:
            return None, "invalid_script_name"
        script_path = os.path.join(CAPABILITIES_DIR, script_name + ".py")
        if not os.path.isfile(script_path):
            return None, "script_not_found"
        with self._lock:
            if self._proc and self._proc.poll() is None:
                return None, "already_running"
            self._output.clear()
            run_id = uuid.uuid4().hex[:8]
            self._run_id = run_id
            cmd = ["python3", script_path]
            if OFFLINE:
                cmd.append("--offline")
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self._reader, daemon=True).start()
        return run_id, None

    def _reader(self):
        for line in self._proc.stdout:
            self._output.append(line.rstrip())
        self._proc.stdout.close()

    def run_shell(self, script):
        with self._lock:
            if self._proc and self._proc.poll() is None:
                return None, "already_running"
            self._output.clear()
            run_id = uuid.uuid4().hex[:8]
            self._run_id = run_id
            self._proc = subprocess.Popen(
                ["bash", "-c", script],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=os.environ.copy())
        threading.Thread(target=self._reader, daemon=True).start()
        return run_id, None

    def stop(self):
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()

    def stream(self, run_id):
        if run_id != self._run_id:
            return
        sent = 0
        last_heartbeat = time.time()
        while True:
            current = list(self._output)
            while sent < len(current):
                yield f"data: {current[sent]}\n\n"
                sent += 1
            if self._proc and self._proc.poll() is not None and sent >= len(self._output):
                yield "data: [done]\n\n"
                break
            if time.time() - last_heartbeat > 15:
                yield ": keep-alive\n\n"
                last_heartbeat = time.time()
            time.sleep(0.1)

    def status(self):
        if self._proc is None:
            return "idle"
        return "running" if self._proc.poll() is None else "idle"


# ── Capability Scanner ─────────────────────────────────────────────────────────
def scan_capabilities():
    caps = []
    if not os.path.isdir(CAPABILITIES_DIR):
        return caps
    for fname in sorted(os.listdir(CAPABILITIES_DIR)):
        if not fname.endswith(".py"):
            continue
        script = fname[:-3]
        path = os.path.join(CAPABILITIES_DIR, fname)
        try:
            with open(path) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name) and t.id == "META":
                            meta = ast.literal_eval(node.value)
                            caps.append({
                                "script": script,
                                "name": meta.get("name", script),
                                "icon": meta.get("icon", "▶"),
                                "description": meta.get("description", ""),
                            })
        except Exception:
            pass
    return caps


# ── Recording summary ──────────────────────────────────────────────────────────
def _compute_recording_summary(samples):
    if not samples:
        return {"note": "No data — was robot connected during recording?"}
    duration = round(samples[-1]["t"], 2)
    joints_moved = []
    for i, name in enumerate(JOINT_NAMES):
        qs = [s["joints"][i][0] for s in samples if i < len(s.get("joints", []))]
        if len(qs) < 2:
            continue
        rng = max(qs) - min(qs)
        if rng > 0.05:
            taus = [abs(s["joints"][i][2]) for s in samples if i < len(s.get("joints", []))]
            joints_moved.append({
                "idx": i, "name": name,
                "range_rad": round(rng, 3),
                "range_deg": round(math.degrees(rng), 1),
                "peak_tau":  round(max(taus), 2),
            })
    transitions = []
    prev_mode = None
    for s in samples:
        cur = (s.get("mode"), s.get("sport"))
        if cur != prev_mode:
            transitions.append({"t": s["t"], "mode_id": s.get("mode"), "sport_mode": s.get("sport")})
            prev_mode = cur

    # Detect gesture events from arm_action changes
    gestures_detected = []
    prev_gesture = None
    for s in samples:
        g = s.get("gesture", {})
        name = g.get("name", "")
        holding = g.get("holding", False)
        if holding and name and name != prev_gesture:
            gestures_detected.append({"t": s["t"], "name": name, "id": g.get("id", 0)})
        prev_gesture = name if holding else None

    return {
        "duration_s": duration,
        "sample_count": len(samples),
        "joints_moved": joints_moved,
        "mode_transitions": transitions,
        "gestures_detected": gestures_detected,
    }


# ── Flask init ─────────────────────────────────────────────────────────────────
if ROS_AVAILABLE:
    try:
        rclpy.init()
    except Exception:
        ROS_AVAILABLE = False
        OFFLINE = True

try:
    health_monitor = HealthMonitor()
except Exception as e:
    print(f"[Robot Control] ROS node failed ({e}) — falling back to OFFLINE mode")
    ROS_AVAILABLE = False
    OFFLINE = True
    health_monitor = HealthMonitor()

process_manager = ProcessManager()


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def api_health():
    return jsonify(health_monitor.to_dict())


@app.route("/api/capabilities")
def api_capabilities():
    return jsonify(scan_capabilities())


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(silent=True) or {}
    script = data.get("script", "")
    run_id, err = process_manager.run(script)
    if err:
        code = 409 if err == "already_running" else 400
        return jsonify({"error": err}), code
    return jsonify({"run_id": run_id})


@app.route("/api/output/<run_id>")
def api_output(run_id):
    return Response(
        process_manager.stream(run_id),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/stop", methods=["POST"])
def api_stop():
    process_manager.stop()
    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    return jsonify({"status": process_manager.status(), "recording": health_monitor.is_recording()})


@app.route("/api/forceStop", methods=["POST"])
def api_force_stop():
    process_manager.stop()
    return jsonify({"ok": True})


@app.route("/api/runcommands", methods=["POST"])
def api_runcommands():
    import re
    repo = os.path.dirname(__file__)
    subprocess.run(["git", "fetch", "origin", "-q"], cwd=repo, capture_output=True)
    subprocess.run(["git", "reset", "--hard", "origin/main", "-q"], cwd=repo, capture_output=True)
    cmd_file = os.path.join(repo, "COMMANDS.md")
    if not os.path.exists(cmd_file):
        return jsonify({"error": "COMMANDS.md not found"}), 404
    with open(cmd_file) as f:
        content = f.read()
    blocks = re.findall(r"```bash\n(.*?)```", content, re.DOTALL)
    if not blocks:
        return jsonify({"error": "No bash blocks found in COMMANDS.md"}), 400
    run_id, err = process_manager.run_shell("\n".join(blocks))
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"run_id": run_id})


@app.route("/api/savelog", methods=["POST"])
def api_savelog():
    data = request.get_json(silent=True) or {}
    log_content = data.get("log", "")
    try:
        output_path = os.path.join(os.path.dirname(__file__), "OUTPUT.md")
        with open(output_path, "w") as f:
            f.write("# Log Output\n\n```\n")
            f.write(log_content)
            f.write("\n```\n")
        repo = os.path.dirname(__file__)
        subprocess.run(["git", "add", "OUTPUT.md"], cwd=repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "save log"], cwd=repo, capture_output=True)
        subprocess.run(["git", "push"], cwd=repo, capture_output=True)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    process_manager.stop()
    def _shutdown():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_shutdown, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/api/record/start", methods=["POST"])
def api_record_start():
    if OFFLINE:
        return jsonify({"ok": True, "offline": True,
                        "note": "Offline mode — no real data will be captured"})
    stats_before = health_monitor.recording_stats()
    health_monitor.start_recording()
    return jsonify({"ok": True, "cb_count_at_start": stats_before["cb_count"]})


@app.route("/api/record/stop", methods=["POST"])
def api_record_stop():
    data = request.get_json(silent=True) or {}
    label = data.get("label", "session")
    label = "".join(c for c in label if c.isalnum() or c in "_-")[:32] or "session"
    samples = health_monitor.stop_recording()
    summary = _compute_recording_summary(samples)

    if not samples:
        return jsonify({"ok": True, "samples": 0, "summary": summary})

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    filename = f"{ts}_{label}.json"
    with open(os.path.join(recordings_dir, filename), "w") as f:
        _json.dump({"label": label, "timestamp": ts,
                    "joint_names": JOINT_NAMES, "samples": samples}, f)

    return jsonify({"ok": True, "file": filename, "samples": len(samples), "summary": summary,
                    "cb_count_total": health_monitor.recording_stats()["cb_count"]})


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    health_monitor.start()
    mode = "OFFLINE" if OFFLINE else "LIVE"
    print(f"[Robot Control] Starting in {mode} mode")
    print(f"[Robot Control] Open http://localhost:5000 in your browser")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
