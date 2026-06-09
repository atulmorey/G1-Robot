#!/usr/bin/env python3
"""
Scan point cloud and print min/max bounds.
Helps calibrate ROI for object detection.
Run: python3 ~/G1-Robot/g1_scan_bounds.py
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointCloud2
import numpy as np
import struct
import time


def parse_pointcloud2(msg):
    points = []
    point_step = msg.point_step
    data = msg.data
    offsets = {}
    for field in msg.fields:
        if field.name in ('x', 'y', 'z'):
            offsets[field.name] = field.offset
    if not all(k in offsets for k in ('x', 'y', 'z')):
        return np.array([])
    ox, oy, oz = offsets['x'], offsets['y'], offsets['z']
    for i in range(msg.width * msg.height):
        base = i * point_step
        x = struct.unpack_from('f', data, base + ox)[0]
        y = struct.unpack_from('f', data, base + oy)[0]
        z = struct.unpack_from('f', data, base + oz)[0]
        if not (np.isnan(x) or np.isnan(y) or np.isnan(z)):
            if abs(x) < 10 and abs(y) < 10 and abs(z) < 10:
                points.append([x, y, z])
    return np.array(points) if points else np.array([])


class BoundsScanner(Node):
    def __init__(self):
        super().__init__("bounds_scanner")
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(
            PointCloud2, "/utlidar/cloud_livox_mid360", self.cb, qos)
        self.last_print = 0
        print("Scanning point cloud bounds... Ctrl+C to stop\n")

    def cb(self, msg):
        now = time.time()
        if now - self.last_print < 2.0:
            return
        self.last_print = now

        points = parse_pointcloud2(msg)
        if len(points) == 0:
            print("No valid points")
            return

        print(f"Total valid points: {len(points)}")
        print(f"  X: min={points[:,0].min():.2f}  max={points[:,0].max():.2f}  mean={points[:,0].mean():.2f}")
        print(f"  Y: min={points[:,1].min():.2f}  max={points[:,1].max():.2f}  mean={points[:,1].mean():.2f}")
        print(f"  Z: min={points[:,2].min():.2f}  max={points[:,2].max():.2f}  mean={points[:,2].mean():.2f}")

        # Show Z histogram to find table plane
        hist, edges = np.histogram(points[:,2], bins=20)
        print("\n  Z distribution (height histogram):")
        for i in range(len(hist)):
            bar = '#' * (hist[i] // 200)
            print(f"    z={edges[i]:+.2f} to {edges[i+1]:+.2f}: {bar} ({hist[i]})")
        print()


def main():
    rclpy.init()
    node = BoundsScanner()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
