#!/usr/bin/env python3
"""
G1 Joystick Button Decoder
Prints human-readable button names in real time.
Run: python3 ~/g1_buttons.py
"""
import rclpy
from rclpy.node import Node
from unitree_go.msg import WirelessController

BUTTON_MAP = {
    1:    "R1",
    2:    "L1",
    4:    "Start",
    8:    "Select",
    16:   "R2",
    32:   "L2",
    256:  "A",
    512:  "B",
    1024: "X",
    2048: "Y",
}

def decode_keys(keys):
    pressed = [name for bit, name in BUTTON_MAP.items() if keys & bit]
    return " + ".join(pressed) if pressed else None

class ButtonDecoder(Node):
    def __init__(self):
        super().__init__("button_decoder")
        self.last_keys = 0
        self.create_subscription(
            WirelessController, "/wirelesscontroller", self.cb, 10)
        print("Listening for joystick input... (Ctrl+C to stop)\n")

    def cb(self, msg):
        if msg.keys != self.last_keys:
            self.last_keys = msg.keys
            buttons = decode_keys(msg.keys)
            if buttons:
                print(f"  PRESSED:  {buttons}  (keys={msg.keys})")
            else:
                print(f"  RELEASED")

def main():
    rclpy.init()
    node = ButtonDecoder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == "__main__":
    main()
