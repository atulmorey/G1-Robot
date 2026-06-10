#!/usr/bin/env python3
META = {
    "name": "Detect Objects",
    "icon": "👁️",
    "description": "LiDAR scan — detects objects on table and prints 3D coordinates.",
}

import sys
import time
import struct
import numpy as np

OFFLINE = "--offline" in sys.argv

if not OFFLINE:
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import PointCloud2
        ROS_AVAILABLE = True
    except ImportError:
        ROS_AVAILABLE = False
        OFFLINE = True
else:
    ROS_AVAILABLE = False

ROI_X_MIN = -2.0
ROI_X_MAX = 1.0
ROI_Y_MIN = -3.0
ROI_Y_MAX = 3.0
ROI_Z_MIN = 0.2
ROI_Z_MAX = 1.2
MIN_CLUSTER_POINTS = 30


def parse_pointcloud2(msg):
    points = []
    offsets = {}
    for field in msg.fields:
        if field.name in ('x', 'y', 'z'):
            offsets[field.name] = field.offset
    if not all(k in offsets for k in ('x', 'y', 'z')):
        return np.array([])
    ox, oy, oz = offsets['x'], offsets['y'], offsets['z']
    for i in range(msg.width * msg.height):
        base = i * msg.point_step
        x = struct.unpack_from('f', msg.data, base + ox)[0]
        y = struct.unpack_from('f', msg.data, base + oy)[0]
        z = struct.unpack_from('f', msg.data, base + oz)[0]
        if not (np.isnan(x) or np.isnan(y) or np.isnan(z)):
            points.append([x, y, z])
    return np.array(points) if points else np.array([])


def detect(points):
    mask = (
        (points[:, 0] >= ROI_X_MIN) & (points[:, 0] <= ROI_X_MAX) &
        (points[:, 1] >= ROI_Y_MIN) & (points[:, 1] <= ROI_Y_MAX) &
        (points[:, 2] >= ROI_Z_MIN) & (points[:, 2] <= ROI_Z_MAX)
    )
    roi = points[mask]
    if len(roi) < MIN_CLUSTER_POINTS:
        return None, []
    hist, edges = np.histogram(roi[:, 2], bins=30)
    table_z = edges[np.argmax(hist)]
    above = roi[roi[:, 2] > (table_z + 0.05)]
    clusters = []
    used = np.zeros(len(above), dtype=bool)
    for i in range(len(above)):
        if used[i]:
            continue
        dists = np.linalg.norm(above - above[i], axis=1)
        cm = dists < 0.15
        if cm.sum() >= MIN_CLUSTER_POINTS:
            clusters.append({
                'centroid': above[cm].mean(axis=0),
                'size': int(cm.sum()),
                'height': float(above[cm][:, 2].max() - table_z),
            })
            used[cm] = True
    return table_z, clusters


def main():
    if OFFLINE:
        print("OFFLINE: Sample detection from previous session:")
        print("  Table surface at z=0.979m")
        print("  Object 1: x=-0.21m  y=-1.06m  z=1.10m  height=0.21m")
        print("  Object 2: x=0.64m   y=-0.97m  z=1.06m  height=0.11m")
        print("  Object 3: x=0.38m   y=-1.63m  z=1.10m  height=0.17m")
        return

    rclpy.init()

    class ScanNode(Node):
        def __init__(self):
            super().__init__("detect_objects_node")
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
            self.latest = None
            self.create_subscription(PointCloud2, "/utlidar/cloud_livox_mid360",
                                     lambda m: setattr(self, 'latest', m), qos)

    node = ScanNode()
    print("Scanning for objects (5 seconds)...")

    scans = 0
    start = time.time()
    while (time.time() - start) < 5.0:
        rclpy.spin_once(node, timeout_sec=0.2)
        if node.latest:
            points = parse_pointcloud2(node.latest)
            if len(points) > 0:
                table_z, clusters = detect(points)
                if clusters:
                    print(f"  Table surface at z={table_z:.3f}m  |  {len(clusters)} object(s):")
                    for i, c in enumerate(clusters):
                        cx, cy, cz = c['centroid']
                        print(f"    Object {i+1}: x={cx:.2f}m  y={cy:.2f}m  z={cz:.2f}m  "
                              f"height={c['height']:.2f}m  pts={c['size']}")
                    scans += 1
                    if scans >= 3:
                        break
            node.latest = None

    if scans == 0:
        print("No objects detected — point robot toward table.")

    rclpy.shutdown()


if __name__ == "__main__":
    main()
