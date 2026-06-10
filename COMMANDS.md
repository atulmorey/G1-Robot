# Commands — Run these in Ubuntu terminal

## Make multicast route permanent (one time only)
```bash
echo "route add -net 224.0.0.0 netmask 240.0.0.0 dev eno1" | sudo tee -a /etc/rc.local
sudo chmod +x /etc/rc.local
```

## Pull and update desktop file
```bash
cd ~/G1-Robot && git pull
cp ~/G1-Robot/RobotControl.desktop ~/Desktop/
chmod +x ~/Desktop/RobotControl.desktop
```

## Then double-click the desktop icon
