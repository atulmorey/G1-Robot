# Commands

```bash
echo "=== 1. Arm Joint Positions (fixed) ==="
python3 - <<'PYEOF'
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from unitree_hg.msg import LowState

rclpy.init()
class QuickCheck(Node):
    def __init__(self):
        super().__init__('quick_check')
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.msg = None
        self.create_subscription(LowState, '/lf/lowstate', lambda m: setattr(self, 'msg', m), qos)

n = QuickCheck()
for _ in range(60):
    rclpy.spin_once(n, timeout_sec=0.1)
    if n.msg:
        break

if n.msg:
    joints = n.msg.motor_state
    # Introspect available fields on first joint
    print("MotorState fields:", [f for f in dir(joints[0]) if not f.startswith('_')])
    print()
    labels = {22: "R_shoulder_pitch", 23: "R_shoulder_roll", 24: "R_shoulder_yaw", 25: "R_elbow", 26: "R_wrist_roll"}
    print("Right arm joints:")
    for i in [22, 23, 24, 25, 26]:
        j = joints[i]
        # Use tau_est (G1 uses estimated torque, not commanded tau)
        torque = getattr(j, 'tau_est', getattr(j, 'tau', 'N/A'))
        print(f"  [{i}] {labels[i]}: q={j.q:.3f} rad  dq={j.dq:.3f} rad/s  tau_est={torque}")
    print(f"\nIMU: roll={n.msg.imu_state.rpy[0]:.3f}  pitch={n.msg.imu_state.rpy[1]:.3f}  yaw={n.msg.imu_state.rpy[2]:.3f}")
    print(f"mode_machine: {n.msg.mode_machine}")
else:
    print("ERROR: No LowState received")
rclpy.shutdown()
PYEOF

echo ""
echo "=== 2. Can we send to /armsdk? (dry-run check) ==="
python3 - <<'PYEOF'
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from unitree_hg.msg import LowCmd

rclpy.init()
class ArmCheck(Node):
    def __init__(self):
        super().__init__('arm_check')
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.pub = self.create_publisher(LowCmd, '/armsdk', qos)

n = ArmCheck()
# Check publisher count (how many subscribers are listening on /armsdk)
rclpy.spin_once(n, timeout_sec=0.5)
count = n.pub.get_subscription_count()
print(f"/armsdk publisher created OK")
print(f"Subscribers on /armsdk: {count}")
if count > 0:
    print("Robot arm SDK is listening — ready to receive commands")
else:
    print("WARNING: No subscribers on /armsdk — arm SDK may not be active")
    print("Try: stand the robot up first, then the arm SDK activates")
rclpy.shutdown()
PYEOF

echo ""
echo "=== 3. What mode is the robot in right now? ==="
python3 - <<'PYEOF'
import rclpy, time
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from unitree_hg.msg import LowState
try:
    from unitree_go.msg import SportModeState
    HAS_SPORT = True
except:
    HAS_SPORT = False

rclpy.init()
class ModeCheck(Node):
    def __init__(self):
        super().__init__('mode_check')
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.low = None
        self.sport = None
        self.create_subscription(LowState, '/lf/lowstate', lambda m: setattr(self, 'low', m), qos)
        if HAS_SPORT:
            self.create_subscription(SportModeState, '/lf/sportmodestate', lambda m: setattr(self, 'sport', m), qos)

n = ModeCheck()
for _ in range(80):
    rclpy.spin_once(n, timeout_sec=0.1)
    if n.low and (n.sport or not HAS_SPORT):
        break

MODE_NAMES = {0:"IDLE",1:"BALANCE_STAND",2:"POSE",3:"LOCOMOTION",5:"JOINT_LOCK",6:"DAMPING",7:"RECOVERY_STAND",9:"SIT"}
SPORT_MODES = {0:"IDLE",1:"BALANCE_STAND",2:"POSE",3:"LOCOMOTION",5:"LIE_DOWN",6:"JOINT_LOCK",7:"DAMPING",8:"RECOVERY_STAND",10:"SIT"}

if n.low:
    mm = int(n.low.mode_machine)
    print(f"LowState mode_machine: {mm} = {MODE_NAMES.get(mm, 'unknown')}")
else:
    print("No LowState")

if n.sport:
    sm = int(n.sport.mode)
    gt = int(n.sport.gait_type)
    print(f"SportModeState: mode={sm} ({SPORT_MODES.get(sm,'unknown')})  gait={gt}")
else:
    print("No SportModeState — robot not in sport/locomotion mode")

print()
print("NEXT STEP: To enable arm control, robot must be standing (mode=BALANCE_STAND)")
print("Use 'Stand Up' button in web UI, then re-run diagnostics")
rclpy.shutdown()
PYEOF

echo ""
echo "=== Done ==="
```
