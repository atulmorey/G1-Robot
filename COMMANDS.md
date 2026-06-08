# Commands — Run these in Ubuntu terminal

## Restore robot to ai mode
```bash
source ~/unitree_ros2/setup.sh
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
python3 -c "
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from unitree_api.msg import Request
import json, time
rclpy.init()
node = Node('restore')
pub = node.create_publisher(Request, '/api/motion_switcher/request', 10)
time.sleep(1)
msg = Request()
msg.header.identity.api_id = 1002
msg.parameter = json.dumps({'name': 'ai'})
pub.publish(msg)
time.sleep(2)
print('ai mode restored')
rclpy.shutdown()
"
```
