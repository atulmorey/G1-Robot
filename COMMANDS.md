# Commands — Run these in Ubuntu terminal

```bash
ls ~/G1-Robot/templates/
find ~/G1-Robot/templates -name "*.cache" -o -name "__pycache__" 2>/dev/null
curl -s http://localhost:5000 | grep -c "savelog"
curl -s http://localhost:5000 | wc -c
```
