# Commands — Run these in Ubuntu terminal

## Check motion switcher response
```bash
ros2 topic info /api/motion_switcher/response
```

## Check what mode robot is currently in
```bash
ros2 topic echo /api/motion_switcher/response --once
```

## Check sportmodestate for current mode
```bash
ros2 topic echo /lf/sportmodestate --once
```
