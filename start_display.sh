#!/bin/bash
# Start RPIFrame display on local console

# Export display for local console
export DISPLAY=:0

# Kill any existing processes
/usr/bin/python3 /home/spencer/RPIFrame/stop_all.py

# Start the application
cd /home/spencer/RPIFrame
/usr/bin/python3 run.py > /home/spencer/RPIFrame/logs/startup.log 2>&1 &

echo "RPIFrame started. Check logs/startup.log for details."
echo "To stop: python3 stop_all.py"