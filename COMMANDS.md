# Commands — Run these in Ubuntu terminal

```bash
ping -c 2 192.168.123.161 && echo "Robot reachable" || echo "Robot NOT reachable"
```

```bash
ros2 topic list > /tmp/topics.txt && cat /tmp/topics.txt | grep -E "video|lidar|utlidar|camera" && echo "---" && wc -l /tmp/topics.txt
```
