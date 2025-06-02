#!/bin/bash
#
# Update RPIFrame service to work with fbi
#

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Updating RPIFrame service configuration...${NC}"

# Create sudoers rule for fbi
sudo tee /etc/sudoers.d/rpiframe > /dev/null << EOF
# Allow rpiframe to run fbi without password
$USER ALL=(ALL) NOPASSWD: /usr/bin/fbi
$USER ALL=(ALL) NOPASSWD: /usr/bin/pkill fbi
EOF

# Update service file to allow fbi
sudo tee /etc/systemd/system/rpiframe.service > /dev/null << EOF
[Unit]
Description=RPIFrame DSI Photo Frame
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=video
WorkingDirectory=/home/$USER/RPIFrame

# Environment
Environment="PATH=/home/$USER/RPIFrame/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=/home/$USER/RPIFrame"
Environment="HOME=/home/$USER"

# Add capability to access framebuffer
SupplementaryGroups=video
PrivateDevices=no

# Start command
ExecStartPre=/bin/sleep 10
ExecStart=/home/$USER/RPIFrame/venv/bin/python /home/$USER/RPIFrame/main.py

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Logging
StandardOutput=append:/home/$USER/RPIFrame/logs/rpiframe.log
StandardError=append:/home/$USER/RPIFrame/logs/rpiframe-error.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo -e "${GREEN}✓ Service configuration updated${NC}"
echo "The service can now use fbi for framebuffer display"