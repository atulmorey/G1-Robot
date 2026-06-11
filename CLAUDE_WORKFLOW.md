# CLAUDE_WORKFLOW.md

This file documents exactly how Claude and the G1-Robot project work together. Share at the start of future sessions so Claude can immediately resume without re-learning anything.

---

## 1. Project Overview

- **Robot:** Unitree G1 humanoid — 29 DOF, onboard Livox Mid-360 LiDAR, onboard speaker, Dex3 hands
- **Ubuntu laptop:** Dell i9, Quadro P1000, Ubuntu 22.04, ROS 2 Humble — connected to robot via Ethernet (192.168.123.x), on open WiFi (NOT on corporate network)
- **Windows laptop:** Dell i9 — on corporate network, runs Claude Code
- **Web app:** Flask app on Ubuntu at `localhost:5000` — browser-based robot control
- **Phase 1 goal:** Robot autonomously touches a randomly placed object ≥ 90% of the time
- **Robot's name:** Wilson

---

## 2. GitHub Token Setup (ONE-TIME — already configured)

The token is stored permanently. Claude does NOT need to ask for it each session.

```powershell
# Read token (already stored — works in any new PowerShell session)
$env:GITHUB_TOKEN = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "User")
$headers = @{ Authorization = "Bearer $env:GITHUB_TOKEN" }
```

**When token is rotated**, run these two commands once (replace `ghp_NEW`):
```powershell
[Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "ghp_NEW", "User")
$pair = "x-access-token:ghp_NEW"
$b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($pair))
git config --global http.https://github.com/.extraheader "Authorization: Basic $b64"
```

**Git global config (already set — no flags needed):**
- `http.sslBackend = schannel` — handles corporate SSL inspection
- `http.https://github.com/.extraheader` — Authorization header with token
- `credential.helper = ""` — no TTY prompt

---

## 3. How Claude Pushes Code to Ubuntu

**Read a file:**
```powershell
$env:GITHUB_TOKEN = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "User")
$headers = @{ Authorization = "Bearer $env:GITHUB_TOKEN" }
$file = Invoke-RestMethod "https://api.github.com/repos/atulmorey/G1-Robot/contents/COMMANDS.md" -Headers $headers
[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($file.content))
```

**Write/update a file:**
```powershell
$env:GITHUB_TOKEN = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "User")
$headers = @{ Authorization = "Bearer $env:GITHUB_TOKEN" }
$file = Invoke-RestMethod "https://api.github.com/repos/atulmorey/G1-Robot/contents/PATH" -Headers $headers
$sha = $file.sha
$content = Get-Content "C:\path\to\local\file" -Raw -Encoding UTF8
$encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
$body = @{ message = "commit message"; content = $encoded; sha = $sha } | ConvertTo-Json
$result = Invoke-RestMethod "https://api.github.com/repos/atulmorey/G1-Robot/contents/PATH" -Method Put -Headers $headers -Body $body
Write-Output "Pushed: $($result.commit.sha.Substring(0,7))"
```

**Push multiple files at once (use this pattern):**
```powershell
$pushes = @(
    @{ path="server.py"; local="C:\Users\amore159443\AppData\Local\Temp\G1-Robot\server.py"; msg="commit msg" },
    @{ path="COMMANDS.md"; local="C:\...\COMMANDS.md"; msg="commit msg" }
)
foreach ($p in $pushes) {
    $file = Invoke-RestMethod "https://api.github.com/repos/atulmorey/G1-Robot/contents/$($p.path)" -Headers $headers
    $sha = $file.sha
    $content = Get-Content $p.local -Raw -Encoding UTF8
    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
    $body = @{ message = $p.msg; content = $encoded; sha = $sha } | ConvertTo-Json
    $result = Invoke-RestMethod "https://api.github.com/repos/atulmorey/G1-Robot/contents/$($p.path)" -Method Put -Headers $headers -Body $body
    Write-Output "OK $($p.path) -> $($result.commit.sha.Substring(0,7))"
}
```

**Clone repo locally on Windows (if needed for multi-file edits):**
```powershell
cd $env:TEMP
git clone https://github.com/atulmorey/G1-Robot.git
# Files land at: C:\Users\amore159443\AppData\Local\Temp\G1-Robot\
```

---

## 4. The Dev Loop (Claude → Ubuntu → Claude)

1. Claude edits files locally (`$env:TEMP\G1-Robot\`) and pushes via GitHub API
2. User double-clicks **desktop launcher** on Ubuntu → `git pull` + server restart
3. OR user clicks **Run Commands** in browser → `git pull` + executes `COMMANDS.md` bash blocks
4. User clicks **Save Log** → `OUTPUT.md` committed + pushed to GitHub
5. User pastes commit URL/hash → Claude reads `OUTPUT.md` at that exact commit:

```powershell
$file = Invoke-RestMethod "https://api.github.com/repos/atulmorey/G1-Robot/contents/OUTPUT.md?ref=COMMIT_HASH" -Headers $headers
[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($file.content))
```

**CRITICAL:** Run Commands does `git pull` but does NOT restart server.py. New server.py code only takes effect after the desktop launcher is double-clicked. Always restart the server when server.py changes.

---

## 5. COMMANDS.md Format

All ` ```bash ` blocks are concatenated and run as one script. Push before asking user to click Run Commands.

```markdown
```bash
echo "check something"
ros2 topic list
```
```

---

## 6. Repo Structure

```
G1-Robot/
├── capabilities/              # Auto-discovered — each .py = one button in web UI
│   ├── touch_object.py        # Full pipeline: LiDAR detect -> IK -> right arm -> return home
│   ├── detect_objects.py      # LiDAR point cloud object detection
│   ├── show_joint_map.py      # Prints all 29 joints (q, dq, tau_est) + full IMU snapshot
│   ├── stand_up.py            # Switch to BALANCE_STAND via motion_switcher
│   ├── sit_down.py            # Switch to AI/rest mode
│   ├── wave_right_arm.py      # Direct joint control
│   ├── wave_left_arm.py       # Direct joint control
│   └── play_audio.py          # Plays audio via onboard speaker
├── recordings/                # JSON files saved by Start/Stop recording (created on first use)
├── server.py                  # Flask web app, HealthMonitor ROS node, recording engine
├── templates/index.html       # Web UI — Record/Stop buttons, live health panel
├── COMMANDS.md                # Claude writes bash blocks here -> Run Commands executes them
├── OUTPUT.md                  # Ubuntu writes logs here -> Claude reads via commit hash
├── CLAUDE_WORKFLOW.md         # This file
├── generate_timeline.py       # Generates G1_Phase1_Timeline.pptx — run on WINDOWS not Ubuntu
├── g1_moveit_config/          # Hand-written MoveIt 2 config (Setup Assistant crashed on Quadro P1000)
└── launch_robot_app.sh        # Desktop launcher: git pull + kill old server + start fresh
```

---

## 7. ROS 2 Key Facts

**Connection:**
- DDS: CycloneDDS 0.10.x, config: `~/cyclone_g1.xml`, interface: `eno1`
- `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, `CYCLONEDDS_URI=file://$HOME/cyclone_g1.xml`
- Multicast route must be re-added after reboot (rc.local configured)

**Key topics (confirmed active):**

| Topic | Type | Hz | Notes |
|-------|------|----|-------|
| `/lf/lowstate` | `unitree_hg/msg/LowState` | 20 Hz | All joints + IMU — primary data source |
| `/lf/sportmodestate` | two types (conflict!) | — | Only publishes when robot is in sport mode |
| `/utlidar/cloud_livox_mid360` | `sensor_msgs/msg/PointCloud2` | 10 Hz | 20,064 pts/scan |
| `/armsdk` | `unitree_hg/msg/LowCmd` | — | Send arm joint commands here |
| `/arm/action/state` | `std_msgs/msg/String` | — | JSON: `{"holding":bool,"id":int,"name":str}` — KEY for gesture detection |
| `/api/gesture/request` | `unitree_api/msg/Request` | — | Programmatic gesture trigger |
| `/api/motion_switcher/request` | `unitree_api/msg/Request` | — | Mode switching |
| `/wirelesscontroller` | `unitree_go/msg/WirelessController` | — | Controller button states |
| `/dog_odom` | `nav_msgs/msg/Odometry` | — | Robot odometry, z≈0.736m when standing |
| `/lf/bmsstate` | `unitree_hg/msg/BmsState` | — | Battery: 11 cells, ~3960mV each ≈ 90% |
| `/dex3/left/cmd`, `/dex3/right/cmd` | `unitree_hg/msg/HandCmd` | — | Hand control |

**`/lf/sportmodestate` type conflict** — topic has two types registered:
- `unitree_go/msg/SportModeState` and `unitree_hg/msg/SportModeState`
- Neither publishes when robot is in JOINT_LOCK (mode_machine=5)
- Subscribe with `unitree_go/msg/SportModeState` for sport mode data

**LowState message structure:**
- `motor_state[i].q` — joint position (rad)
- `motor_state[i].dq` — joint velocity (rad/s)
- `motor_state[i].tau_est` — estimated torque (Nm) — NOT `.tau`
- `imu_state.rpy[0/1/2]` — roll, pitch, yaw (rad)
- `imu_state.acc[0/1/2]` — accelerometer (m/s²), z≈9.81 when upright
- `imu_state.gyro[0/1/2]` — gyroscope (rad/s)
- `mode_machine` — robot mode (see below)

**mode_machine values (from LowState):**
`0=IDLE`, `1=BALANCE_STAND`, `2=POSE`, `3=LOCOMOTION`, `5=JOINT_LOCK`, `6=DAMPING`, `7=RECOVERY_STAND`, `9=SIT`

**Joint map (all 29 joints):**
```
Left leg:   0=L_hip_pitch  1=L_hip_roll  2=L_hip_yaw  3=L_knee  4=L_ankle_pitch  5=L_ankle_roll
Right leg:  6=R_hip_pitch  7=R_hip_roll  8=R_hip_yaw  9=R_knee  10=R_ankle_pitch 11=R_ankle_roll
Waist:      12=waist_yaw   13=waist_roll  14=waist_pitch
Left arm:   15=L_shoulder_pitch  16=L_shoulder_roll  17=L_shoulder_yaw  18=L_elbow
            19=L_wrist_roll  20=L_wrist_pitch  21=L_wrist_yaw
Right arm:  22=R_shoulder_pitch  23=R_shoulder_roll  24=R_shoulder_yaw  25=R_elbow
            26=R_wrist_roll  27=R_wrist_pitch  28=R_wrist_yaw
```

---

## 8. Gesture System

**How gestures work:**
- Triggered by controller button combos (e.g. double-tap X = Kiss gesture)
- Also triggerable via `/api/gesture/request` programmatically
- `/arm/action/state` publishes JSON during any gesture: `{"holding": true, "id": 5, "name": "blow_kiss"}`
- `/gesture/result` topic — result after gesture completes
- Gestures confirmed working: wave, blow_kiss (Kiss), clap, handshake

**Key insight:** The robot does NOT need to be in sport mode to perform gestures. Gestures work in JOINT_LOCK (mode_machine=5).

---

## 9. Start/Stop Recording System

The web app has **● Record** and **■ Stop** buttons in the health panel (left sidebar).

**How it works:**
- `POST /api/record/start` → HealthMonitor begins buffering `/lf/lowstate` samples
- While recording: status field shows `Recording: N samples | gesture: blow_kiss` live
- `POST /api/record/stop` → saves JSON to `~/G1-Robot/recordings/YYYYMMDD_HHMMSS_session.json`
- Stop response includes summary: joints moved (>3 deg), peak torques, gesture events detected

**Recording JSON format:**
```json
{
  "label": "session",
  "timestamp": "20260611_143800",
  "joint_names": ["L_hip_pitch", ...],
  "samples": [
    {
      "t": 0.05,
      "mode": 5,
      "sport": "JOINT_LOCK",
      "gesture": {"holding": true, "id": 5, "name": "blow_kiss"},
      "imu": {"rpy": [...], "acc": [...], "gyro": [...]},
      "joints": [[q, dq, tau_est], ...]  // 29 joints
    }
  ]
}
```

**Debugging empty recordings:**
- After clicking Record, log shows: `LowState callbacks before record: NNN`
- If NNN = 0 → server is not receiving robot data → restart the server
- If NNN > 0 → recording is live, samples should accumulate
- The live counter `Recording: N samples` updates every second while recording

**CRITICAL:** Server must be restarted (desktop launcher) after any push to server.py. Run Commands only updates files on disk, not the running process.

---

## 10. Analysing Recordings via COMMANDS.md

After recording, update COMMANDS.md with this to analyse the latest file:

```bash
python3 - <<'PYEOF'
import os, json, math
recordings_dir = os.path.expanduser("~/G1-Robot/recordings")
files = sorted([f for f in os.listdir(recordings_dir) if f.endswith('.json')])
latest = files[-1]
print(f"File: {latest}")
with open(os.path.join(recordings_dir, latest)) as f:
    data = json.load(f)
samples = data["samples"]
joint_names = data["joint_names"]
print(f"Samples: {len(samples)}  Duration: {samples[-1]['t']:.1f}s")
for i, name in enumerate(joint_names):
    qs = [s["joints"][i][0] for s in samples]
    rng = max(qs) - min(qs)
    if rng > 0.05:
        taus = [abs(s["joints"][i][2]) for s in samples]
        print(f"  [{i:2d}] {name:<22} range={math.degrees(rng):5.1f}deg  peak_tau={max(taus):.2f}Nm")
PYEOF
```

---

## 11. Presentation

`generate_timeline.py` generates the PowerPoint. **Run it on Windows, not Ubuntu** (the output path is a Windows path):

```powershell
python "$env:TEMP\G1-Robot\generate_timeline.py"
# Saves to: C:\Users\amore159443\G1_Phase1_Timeline.pptx
```

If the local clone is stale, pull first:
```powershell
cd "$env:TEMP\G1-Robot"; git pull
```

---

## 12. Current Status (as of 2026-06-11)

**Phase 1 progress:**
- Day 1 DONE: ROS 2 + SDK, robot speaks on command
- Day 2 DONE: Livox LiDAR streaming at 10 Hz, 20,064 pts/scan
- Day 3 DONE: Motion planning pipeline (g1_plan_touch.py), object detection live
- Day 4 IN PROGRESS: Physical arm movement — arm SDK topic active, mode_machine=5 (JOINT_LOCK)
- Day 5 PENDING: Contact detection & safety
- Day 6 PENDING: Full integration demo ≥ 90%

**Robot state baseline:**
- mode_machine: 5 (JOINT_LOCK) — robot standing but not in active motion control
- LowState: 20 Hz exactly (min 0.049s, max 0.051s)
- LiDAR: 10 Hz, 20,064 points/scan, frame: `livox_frame`
- Battery: 11 cells × ~3960mV ≈ 90% charge
- Odometry: robot center z=0.736m when standing
- IMU baseline: acc.z ≈ 9.81 m/s² (confirmed upright)

**Week 2 achievements:**
- Robot Control App fully operational (browser-based, auto-discovers capabilities)
- 100+ ROS topics mapped and documented
- Start/Stop recording system built (captures all 29 joints at 20 Hz)
- Gesture system identified: /arm/action/state is the key topic
- Wilson successfully performed Kiss gesture (double-tap X on controller)
- Dev cycle reduced from 10 min to 30 sec
- Git token setup permanent (no more manual token entry)

**Pending/In progress:**
- Recording returning empty samples — needs debugging (cb_count diagnostic added)
- /arm/action/state subscription added to server for gesture labelling
- sport mode topic type conflict not yet resolved

---

## 13. Session Startup Checklist

1. Load token: `$env:GITHUB_TOKEN = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN", "User")`
2. Read latest OUTPUT.md to see last robot state
3. Check `recordings/` directory for any saved gesture data
4. Ask user what to work on next
