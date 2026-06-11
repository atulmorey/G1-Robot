# CLAUDE_WORKFLOW.md

This file documents exactly how Claude and the G1-Robot project work together. Share this at the start of future sessions so Claude can immediately resume without re-learning anything.

---

## 1. Project Overview

- Unitree G1 humanoid robot (29 DOF, onboard Livox Mid-360 LiDAR, speaker)
- Ubuntu laptop (Dell i9, Quadro P1000, Ubuntu 22.04, ROS 2 Humble) — connected to robot via Ethernet (192.168.123.x), on open WiFi (NOT on corporate network)
- Windows laptop (Dell i9) — on corporate network, runs Claude Code
- Robot Flask web app runs on Ubuntu at localhost:5000
- Phase 1 goal: Robot autonomously touches a randomly placed object >= 90% of the time

---

## 2. Network Constraints

- Corporate network blocks: USB file transfer, Bluetooth, direct SSH to Ubuntu
- git clone/push over HTTPS requires: `git -c http.sslBackend=schannel` (uses Windows cert store to handle corporate SSL inspection)
- GitHub API via PowerShell `Invoke-RestMethod` works fine (Windows cert store trusts corporate CA)
- Ubuntu can push/pull GitHub directly (open WiFi, no restrictions)

---

## 3. How Claude Pushes Code to Ubuntu (Windows to Ubuntu)

Step by step with exact PowerShell commands:

**Step A — Read a file from the repo:**
```powershell
$token = "<GITHUB_TOKEN>"
$headers = @{ Authorization = "Bearer $token" }
$file = Invoke-RestMethod -Uri "https://api.github.com/repos/atulmorey/G1-Robot/contents/COMMANDS.md" -Headers $headers
[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($file.content))
```

**Step B — Write/update a file in the repo:**
```powershell
$token = "<GITHUB_TOKEN>"
$headers = @{ Authorization = "Bearer $token" }
# 1. Get current SHA (required for updates)
$file = Invoke-RestMethod -Uri "https://api.github.com/repos/atulmorey/G1-Robot/contents/COMMANDS.md" -Headers $headers
$sha = $file.sha
# 2. Encode new content
$content = Get-Content "C:\path\to\local\file.md" -Raw -Encoding UTF8
$encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
# 3. Push
$body = @{ message = "commit message here"; content = $encoded; sha = $sha } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "https://api.github.com/repos/atulmorey/G1-Robot/contents/COMMANDS.md" -Method Put -Headers $headers -Body $body
Write-Output "Pushed! Commit: $($result.commit.sha)"
```

**Step C — Clone the repo locally on Windows (if needed):**
```powershell
git -c http.sslBackend=schannel clone https://github.com/atulmorey/G1-Robot.git
```

---

## 4. How Claude Reads Output from Ubuntu (Ubuntu to Claude)

The round-trip feedback loop:

1. Claude writes bash commands into `COMMANDS.md` bash blocks and pushes to GitHub
2. User opens localhost:5000 in Ubuntu browser, hits **Run Commands** — this does `git pull` then executes all bash blocks in `COMMANDS.md`
3. User hits **Save Log** — output is written to `OUTPUT.md`, committed, and pushed to GitHub
4. User pastes the commit URL or hash into the Claude conversation
5. Claude reads `OUTPUT.md` at that exact commit:

```powershell
$token = "<GITHUB_TOKEN>"
$headers = @{ Authorization = "Bearer $token" }
$commitHash = "<PASTE_HASH_HERE>"
$file = Invoke-RestMethod -Uri "https://api.github.com/repos/atulmorey/G1-Robot/contents/OUTPUT.md?ref=$commitHash" -Headers $headers
[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($file.content))
```

**Why the commit hash?** OUTPUT.md push can lag — using the commit hash guarantees Claude reads the exact version that was just saved, not a cached older version.

---

## 5. COMMANDS.md Format

The **Run Commands** button on localhost:5000 parses all ` ```bash ` blocks from `COMMANDS.md` and runs them as a single combined bash script. The Ubuntu Flask server (`server.py`) does a `git pull` before running them, so always push `COMMANDS.md` before asking the user to click Run Commands.

````markdown
```bash
echo "example command"
python3 ~/G1-Robot/capabilities/touch_object.py
```
````

Multiple bash blocks are concatenated and run as one script.

---

## 6. Repo Structure

```
G1-Robot/
├── capabilities/          # Auto-discovered — each .py file = one button in web UI
│   ├── touch_object.py    # Full pipeline: LiDAR detect -> IK -> right arm -> return home
│   ├── detect_objects.py  # LiDAR point cloud object detection
│   ├── stand_up.py        # Switch to BALANCE_STAND via motion_switcher
│   ├── sit_down.py        # Switch to AI/rest mode
│   ├── wave_right_arm.py  # Direct joint control: raises joint 22
│   └── play_audio.py      # Plays audio via onboard speaker
├── server.py              # Flask web app (localhost:5000), HealthMonitor ROS node
├── COMMANDS.md            # Claude writes bash blocks here -> Run Commands executes them
├── OUTPUT.md              # Ubuntu writes logs here -> Claude reads via commit hash
├── g1_moveit_config/      # Hand-written MoveIt 2 config (Setup Assistant crashed on Quadro P1000)
└── templates/index.html   # Web UI
```

---

## 7. ROS 2 Key Facts

- DDS: CycloneDDS 0.10.x, config: `~/cyclone_g1.xml`, interface: `eno1`
- Environment: `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, `CYCLONEDDS_URI=file://$HOME/cyclone_g1.xml`
- Key topics: `/lf/lowstate`, `/lf/sportmodestate`, `/armsdk`, `/utlidar/cloud_livox_mid360`
- Arm joints: Right arm = joints 22-26 (shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll)
- QoS: BEST_EFFORT for all robot topics
- MotorState fields: `q` (position), `dq` (velocity), `tau_est` (estimated torque) — NOT `.tau`
- mode_machine values: 0=IDLE, 1=BALANCE_STAND, 5=JOINT_LOCK, 6=DAMPING, 7=RECOVERY_STAND

---

## 8. Current Phase 1 Status (as of 2026-06-11)

- Day 1 - DONE: ROS 2 + SDK setup complete, robot speaks on command
- Day 2 - DONE: G1 onboard Livox LiDAR used (replaced RealSense), 20,064 pts/scan at 10 Hz
- Day 3 - DONE: Motion planning pipeline working (g1_plan_touch.py), object detection live
- Day 4 - IN PROGRESS: Physical arm movement — pipeline ready, arm SDK topic active, robot currently in JOINT_LOCK mode
- Day 5 - PENDING: Contact detection & safety
- Day 6 - PENDING: Full integration demo >= 90% success rate

---

## 9. GitHub Token

The GitHub PAT is required for Claude to push from the Windows machine. Ask the user to provide it at the start of each session. Do NOT store it in this file. Store it only in memory for the duration of the session.

---

## 10. Quick Session Startup Checklist

1. User provides GitHub token
2. Claude reads `OUTPUT.md` to see last known robot state
3. Claude reads `COMMANDS.md` to see last commands run
4. Check memory files for project context
5. Ask user what to work on next
