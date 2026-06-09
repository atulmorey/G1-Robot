# Commands — Run these in a SECOND terminal (keep Setup Assistant open)

## Check if MoveIt is actively processing
```bash
top -bn1 | grep -E "moveit|setup"
```

## Check for any error messages
```bash
ps aux | grep moveit
```
