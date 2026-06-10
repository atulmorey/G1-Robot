#!/usr/bin/env python3
META = {
    "name": "Play Audio",
    "icon": "🔊",
    "description": "Play a beep sound through the robot speaker.",
}

import sys
import os
import time
import subprocess

OFFLINE = "--offline" in sys.argv

AUDIO_BIN = os.path.expanduser(
    "~/unitree_ros2/example/install/unitree_ros2_example/bin/g1_audio_client_example"
)
BEEP_WAV = os.path.expanduser("~/hello.wav")


def main():
    if OFFLINE:
        print("OFFLINE: Audio playback simulated.")
        time.sleep(0.5)
        print("Done.")
        return

    if not os.path.exists(AUDIO_BIN):
        print(f"Audio binary not found: {AUDIO_BIN}")
        sys.exit(1)

    if not os.path.exists(BEEP_WAV):
        print("Generating beep sound...")
        result = subprocess.run(
            ["sox", "-n", BEEP_WAV, "synth", "1", "sine", "880"],
            capture_output=True
        )
        if result.returncode != 0:
            print("Failed to generate beep (is sox installed?)")
            sys.exit(1)

    print("Sending audio to robot speaker...")
    try:
        subprocess.run([AUDIO_BIN, BEEP_WAV], capture_output=True, timeout=5)
        print("Audio sent.")
    except subprocess.TimeoutExpired:
        print("Audio command timed out.")


if __name__ == "__main__":
    main()
