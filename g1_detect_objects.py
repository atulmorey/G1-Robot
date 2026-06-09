#!/usr/bin/env python3
"""
G1 Object Detection from LiDAR Point Cloud
- Reads /utlidar/cloud_livox_mid360
- Filters to table region in front of robot
- Detects objects above table surface
- Prints 3D coordinates of each object centroid

Run:
  source ~/unitree_ros2/setup.sh
  source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
  python3 ~/G1-Robot/g1_detect_objects.py
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointCloud2
import numpy as np
import struct
import time

# ── Region of interest (metres, in robot/lidar frame) ──────────
# Adjust these based on where your table is relative to the robot
ROI_X_MIN = -0.2   # table clusters seen at x=0.1-0.4
ROI_X_MAX = 0.8
ROI_Y_MIN = -1.6   # table is at y≈-1.2 in LiDAR frame
ROI_Y_MAX = -0.7
ROI_Z_MIN = 0.15   # above floor
ROI_Z_MAX = 0.6    # table top + objects

TABLE_Z_THRESHOLD = 0.05   # objects must be at least 5cm above table plane
MIN_CLUSTER_POINTS = 30    # minimum points to count as an object


def parse_pointcloud2(msg):
    """Convert PointCloud2 message to Nx3 numpy array."""
    points = []
    point_step = msg.point_step
    data = msg.data

    # Find x, y, z field offsets
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
            points.append([x, y, z])

    return np.array(points) if points else np.array([])


def filter_roi(points):
    """Filter points to region of interest."""
    if len(points) == 0:
        return points
    mask = (
        (points[:, 0] >= ROI_X_MIN) & (points[:, 0] <= ROI_X_MAX) &
        (points[:, 1] >= ROI_Y_MIN) & (points[:, 1] <= ROI_Y_MAX) &
        (points[:, 2] >= ROI_Z_MIN) & (points[:, 2] <= ROI_Z_MAX)
    )
    return points[mask]


def detect_table_and_objects(points):
    """Detect table plane and objects above it."""
    if len(points) < 20:
        return None, []

    # Find table plane — most common Z height using histogram
    z_vals = points[:, 2]
    hist, edges = np.histogram(z_vals, bins=50)
    table_z = edges[np.argmax(hist)]

    # Points that are part of the table plane (within 3cm)
    table_mask = np.abs(points[:, 2] - table_z) < 0.03
    table_points = points[table_mask]

    # Points above the table
    above_mask = points[:, 2] > (table_z + TABLE_Z_THRESHOLD)
    above_points = points[above_mask]

    if len(above_points) < MIN_CLUSTER_POINTS:
        return table_z, []

    # Simple clustering — group nearby points
    clusters = []
    used = np.zeros(len(above_points), dtype=bool)

    for i in range(len(above_points)):
        if used[i]:
            continue
        # Find points within 15cm
        dists = np.linalg.norm(above_points - above_points[i], axis=1)
        cluster_mask = dists < 0.15
        if cluster_mask.sum() >= MIN_CLUSTER_POINTS:
            cluster = above_points[cluster_mask]
            centroid = cluster.mean(axis=0)
            clusters.append({
                'centroid': centroid,
                'size': len(cluster),
                'height': cluster[:, 2].max() - table_z,
            })
            used[cluster_mask] = True

    return table_z, clusters


class ObjectDetector(Node):
    def __init__(self):
        super().__init__("object_detector")
        qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(
            PointCloud2, "/utlidar/cloud_livox_mid360", self.cb, qos)
        self.last_print = 0
        print("Object detector running... point robot toward table")
        print(f"ROI: x=[{ROI_X_MIN},{ROI_X_MAX}] y=[{ROI_Y_MIN},{ROI_Y_MAX}] z=[{ROI_Z_MIN},{ROI_Z_MAX}]")
        print("Press Ctrl+C to stop\n")

    def cb(self, msg):
        now = time.time()
        if now - self.last_print < 1.0:
            return
        self.last_print = now

        points = parse_pointcloud2(msg)
        if len(points) == 0:
            print("No points received")
            return

        roi_points = filter_roi(points)
        print(f"Total points: {len(points)} | ROI points: {len(roi_points)}")

        if len(roi_points) < 20:
            print("  Not enough points in ROI — point robot toward table\n")
            return

        table_z, objects = detect_table_and_objects(roi_points)

        if table_z is not None:
            print(f"  Table surface detected at z={table_z:.3f}m")

        if not objects:
            print("  No objects detected above table\n")
        else:
            print(f"  {len(objects)} object(s) detected:")
            for i, obj in enumerate(objects):
                cx, cy, cz = obj['centroid']
                print(f"    Object {i+1}: x={cx:.2f}m  y={cy:.2f}m  z={cz:.2f}m  "
                      f"height={obj['height']:.2f}m  points={obj['size']}")
            print()


def main():
    rclpy.init()
    node = ObjectDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()


if __name__ == "__main__":
    main()
