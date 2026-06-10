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
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

CAPABILITIES_DIR = os.path.join(os.path.dirname(__file__), "capabilities")

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


# ── Health Monitor ────────────────────────────────────────────────────────────
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
        if ROS_AVAILABLE:
            qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.create_subscription(LowState, "/lf/lowstate", self._state_cb, qos)

    def _state_cb(self, msg):
        now = time.time()
        with self._lock:
            self._last_msg_time = now
            self._state = {
                "connected": True,
                "offline_mode": False,
                "imu": {
                    "roll":  round(float(msg.imu_state.rpy[0]), 3),
                    "pitch": round(float(msg.imu_state.rpy[1]), 3),
                    "yaw":   round(float(msg.imu_state.rpy[2]), 3),
                },
                "joints": {
                    "left_shoulder":  round(float(msg.motor_state[15].q), 3),
                    "right_shoulder": round(float(msg.motor_state[22].q), 3),
                },
                "last_update": now,
            }

    def to_dict(self):
        if OFFLINE:
            return {
                "connected": False,
                "offline_mode": True,
                "imu": {"roll": 0.051, "pitch": -0.044, "yaw": 2.151},
                "joints": {"left_shoulder": 0.080, "right_shoulder": -0.087},
                "last_update": time.time(),
            }
        with self._lock:
            # watchdog: no message for 3s → disconnected
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
            t = threading.Thread(target=self.spin, daemon=True)
            t.start()


# ── Process Manager ───────────────────────────────────────────────────────────
class ProcessManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None
        self._run_id = None
        self._output = deque(maxlen=500)

    def run(self, script_name):
        # Sanitize: only alphanumeric + underscore, no path traversal
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
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

        threading.Thread(target=self._reader, daemon=True).start()
        return run_id, None

    def _reader(self):
        for line in self._proc.stdout:
            self._output.append(line.rstrip())
        self._proc.stdout.close()

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


# ── Capability Scanner ────────────────────────────────────────────────────────
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


# ── Flask routes ──────────────────────────────────────────────────────────────
if ROS_AVAILABLE:
    rclpy.init()
health_monitor = HealthMonitor()
process_manager = ProcessManager()


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
    return jsonify({"status": process_manager.status()})


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
        subprocess.run(
            ["git", "add", "OUTPUT.md"],
            cwd=os.path.dirname(__file__), capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "save log"],
            cwd=os.path.dirname(__file__), capture_output=True)
        subprocess.run(
            ["git", "push"],
            cwd=os.path.dirname(__file__), capture_output=True)
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


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    health_monitor.start()
    mode = "OFFLINE" if OFFLINE else "LIVE"
    print(f"[Robot Control] Starting in {mode} mode")
    print(f"[Robot Control] Open http://localhost:5000 in your browser")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
