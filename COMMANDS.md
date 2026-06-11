# Commands

```bash
echo "=== ARM ACTION STATE — trigger a gesture NOW (watching 10s) ==="
timeout 10 ros2 topic echo /arm/action/state 2>&1

echo ""
echo "=== CONTROLLER BUTTONS — press any button NOW (watching 5s) ==="
timeout 5 ros2 topic echo /wirelesscontroller 2>&1 | head -40

echo ""
echo "=== CURRENT RECORDINGS ==="
ls -lah ~/G1-Robot/recordings/ 2>/dev/null || echo "No recordings yet"

echo ""
echo "=== LATEST RECORDING SUMMARY ==="
python3 - <<'PYEOF'
import os, json, math

recordings_dir = os.path.expanduser("~/G1-Robot/recordings")
if not os.path.isdir(recordings_dir):
    print("No recordings directory yet")
    exit()

files = sorted([f for f in os.listdir(recordings_dir) if f.endswith('.json')])
if not files:
    print("No recording files yet")
    exit()

latest = files[-1]
print(f"File: {latest}")

with open(os.path.join(recordings_dir, latest)) as f:
    data = json.load(f)

samples = data.get("samples", [])
joint_names = data.get("joint_names", [])
print(f"Samples: {len(samples)}  Duration: {samples[-1]['t'] if samples else 0:.1f}s")

if not samples:
    print("Empty recording")
    exit()

# Gesture events
print("\nGesture events:")
prev = None
for s in samples:
    g = s.get("gesture", {})
    name = g.get("name", "")
    holding = g.get("holding", False)
    if holding and name and name != prev:
        print(f"  t={s['t']:.2f}s  gesture={name}  id={g.get('id',0)}")
    prev = name if holding else None

# Joints that moved
print("\nJoints that moved (>3 deg):")
moved = False
for i, name in enumerate(joint_names):
    qs = [s["joints"][i][0] for s in samples if i < len(s.get("joints", []))]
    if len(qs) < 2:
        continue
    rng = max(qs) - min(qs)
    if rng > 0.05:
        taus = [abs(s["joints"][i][2]) for s in samples if i < len(s.get("joints", []))]
        print(f"  [{i:2d}] {name:<22}  range={math.degrees(rng):5.1f}deg  peak_tau={max(taus):.2f}Nm")
        moved = True
if not moved:
    print("  None detected")
PYEOF

echo ""
echo "=== Done ==="
```
