#!/bin/bash
# Launch both scripts in their own terminals
lxterminal --title="Control Unit Script" --command="/home/pi/scripts/start_cu.sh"
sleep 5
lxterminal --title="Node-RED" --command="/home/pi/scripts/start_nodered.sh"
sleep 10
# Open Node-RED dashboard in Chromium
chromium-browser http://localhost:1880/ui
