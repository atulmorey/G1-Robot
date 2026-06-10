#!/usr/bin/env python3
META = {
    "name": "Monitor Events",
    "icon": "📡",
    "description": "Live feed of robot API calls via DDS. Press Stop to end.",
}

import sys
import time
import json
import threading

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
        SDK_AVAILABLE = True
    except ImportError:
        SDK_AVAILABLE = False
        OFFLINE = True
else:
    SDK_AVAILABLE = False

SPORT_API_NAMES = {
    1001: "CHECK_MODE",
    1002: "SELECT_MODE",
    1003: "RELEASE_MODE",
    1016: "HELLO/WAVE",
    1009: "SIT",
    1004: "STAND_UP",
    1008: "RECOVERY_STAND",
    1007: "DAMP",
    1005: "STOP_MOVE",
    1006: "BALANCE_STAND",
    7106: "ARM_TASK",
    7105: "SET_VELOCITY",
}


def ts():
    return time.strftime("%H:%M:%S")


def main():
    if OFFLINE:
        print("OFFLINE: Simulating robot events...")
        events = [
            f"[{ts()}] ← SPORT  HELLO/WAVE (api_id=1016)",
            f"[{ts()}] ✓ SPORT  OK",
            f"[{ts()}] ← MOTION_SWITCHER  CHECK_MODE",
            f"[{ts()}] ✓ MOTION_SWITCHER  name=ai",
        ]
        for e in events:
            print(e)
            time.sleep(1)
        print("(Offline demo complete)")
        return

    print(f"[{ts()}] Initializing DDS on eno1...")
    ChannelFactoryInitialize(0, "eno1")

    last_state = {}

    def state_handler(msg):
        mode = msg.mode_machine
        key = "mode_machine"
        if last_state.get(key) != mode:
            last_state[key] = mode
            mode_names = {
                0: "IDLE", 1: "BALANCE_STAND", 2: "POSE",
                3: "LOCOMOTION", 5: "JOINT_LOCK", 6: "DAMPING",
                7: "RECOVERY_STAND", 9: "SIT", 10: "FRONT_FLIP"
            }
            name = mode_names.get(mode, f"mode={mode}")
            print(f"[{ts()}] 🤖 MODE CHANGE → {name} ({mode})")

    sub = ChannelSubscriber("lowstate", LowState_)
    sub.Init(state_handler, 10)

    print(f"[{ts()}] Monitoring robot state changes... (click Stop to end)")
    print(f"[{ts()}] Use controller or web app buttons — mode changes appear here")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
