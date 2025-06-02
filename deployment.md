# RPIFrame Deployment Guide for Raspberry Pi 4

This guide provides step-by-step instructions for deploying RPIFrame on a Raspberry Pi 4 running **Raspberry Pi OS Lite (64-bit)**.

## Prerequisites

- Raspberry Pi 4 (2GB+ RAM)
- Hosyond 7-inch DSI IPS touchscreen (800x480)
- MicroSD card (16GB+ recommended)
- Raspberry Pi OS Lite (64-bit) - Bookworm or later
- Network connection (Ethernet or WiFi configured)
- SSH access to the Pi

## Initial Raspberry Pi Setup

### 1. Flash Raspberry Pi OS Lite

Using Raspberry Pi Imager:
1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select "Raspberry Pi OS Lite (64-bit)"
3. Configure settings (gear icon):
   - Set hostname: `rpiframe`
   - Enable SSH
   - Set username/password
   - Configure WiFi (if needed)
   - Set locale/timezone
4. Write to SD card

### 2. First Boot Configuration

SSH into your Pi:
```bash
ssh pi@rpiframe.local
# or use IP address: ssh pi@192.168.1.xxx
```

Update the system:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

### 3. Enable DSI Display

The Hosyond 7-inch DSI display works plug-and-play with official Raspberry Pi OS. According to the manual:
- **Resolution**: 800×480 pixels
- **Touch Controller**: FT5426 (capacitive, 2-point touch on Raspbian)
- **Interface**: MIPI DSI with RGB888
- **Power**: 3.3V, max 510mA

```bash
sudo nano /boot/firmware/config.txt
```

For **Raspberry Pi 4 with Pi OS Lite**, use FKMS mode (recommended):
```ini
# Enable FKMS (recommended for Pi 4)
dtoverlay=vc4-fkms-v3d
max_framebuffers=2

# Display auto-detection
display_auto_detect=1

# Optional: Force HDMI off to save power
hdmi_force_hotplug=0

# Optional: Reduce GPU memory split (we don't need much for 2D)
gpu_mem=128

# Optional: PWM backlight control (if hardware modified)
# gpio=18=op,pu
```

**Alternative**: For traditional graphics mode (not recommended on Pi 4):
```ini
# Traditional graphics mode (comment out vc4-fkms-v3d)
# dtoverlay=vc4-fkms-v3d
max_framebuffers=2
display_auto_detect=1

# Display rotation (if needed in traditional mode)
# display_lcd_rotate=0  # 0=normal, 1=90°, 2=180°, 3=270°
```

Enable required kernel modules:
```bash
sudo nano /etc/modules
```

Add these lines:
```
i2c-dev
```

Reboot to apply changes:
```bash
sudo reboot
```

## Touch Configuration (Optional)

The FT5426 touch controller should work out-of-the-box. However, if you need to configure touch calibration or rotation:

### Touch Rotation Configuration

If you rotate the display, you may need to adjust touch coordinates. For systems with X11 (not needed for our headless setup):

```bash
sudo nano /usr/share/X11/xorg.conf.d/40-libinput.conf
```

Add calibration matrix based on rotation:
- **Normal**: `Option "CalibrationMatrix" "1 0 0 0 1 0 0 0 1"`
- **90° CW**: `Option "CalibrationMatrix" "0 1 0 -1 0 1 0 0 1"`
- **180°**: `Option "CalibrationMatrix" "-1 0 1 0 -1 1 0 0 1"`
- **270° CW**: `Option "CalibrationMatrix" "0 -1 1 1 0 0 0 0 1"`

### Backlight Control (Advanced)

The display includes hardware backlight control. For PWM control via GPIO18:

1. **Hardware modification required**: Move 0R resistor to PWM position
2. **Wire PWM pin to GPIO18** and GND to Pi's GND
3. **Add to config.txt**: `gpio=18=op,pu`
4. **Control via commands**:
   ```bash
   # Install WiringPi (may be needed on Pi 4)
   cd /tmp
   wget https://project-downloads.drogon.net/wiringpi-latest.deb
   sudo dpkg -i wiringpi-latest.deb
   
   # Control backlight (0-1024 brightness)
   gpio -g mode 18 pwm
   gpio pwmc 1000
   gpio -g pwm 18 512  # 50% brightness
   ```

## Install System Dependencies

### 1. Core System Packages

```bash
# Python and build tools
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y git build-essential

# SDL2 libraries for Pygame (required for Lite)
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install -y libfreetype6-dev libportmidi-dev libjpeg-dev zlib1g-dev libpng-dev

# Additional libraries for headless operation
sudo apt install -y libgbm-dev libdrm-dev libgles2-mesa-dev
sudo apt install -y libatlas-base-dev

# Tools for system management
sudo apt install -y htop iotop
```

### 2. Configure Framebuffer Access

For Pygame to work properly on Lite without X11:

```bash
# Add pi user to video group (should already be member)
sudo usermod -a -G video pi

# Create udev rule for framebuffer access
sudo bash -c 'echo "KERNEL==\"fb*\", GROUP=\"video\", MODE=\"0660\"" > /etc/udev/rules.d/99-framebuffer.rules'

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Deploy RPIFrame

### 1. Clone Repository

```bash
cd /home/pi
git clone https://github.com/yourusername/RPIFrame.git
cd RPIFrame
```

### 2. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip wheel setuptools
```

### 3. Install Python Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# On Raspberry Pi OS Lite, you might need to install Pygame differently:
# If the above fails for pygame, try:
pip install --upgrade pygame --no-binary pygame
```

### 4. Create Required Directories

```bash
mkdir -p photos/thumbnails
mkdir -p logs
```

### 5. Set Permissions

```bash
# Make scripts executable
chmod +x main.py app.py display_slideshow.py test_display.py

# Ensure photo directory is writable
chmod 755 photos
chmod 755 photos/thumbnails
```

## Configure for Headless Operation

### 1. Environment Variables

Create an environment file:
```bash
nano /home/pi/RPIFrame/.env
```

Add:
```bash
# SDL settings for framebuffer
export SDL_VIDEODRIVER=kmsdrm
export SDL_FBDEV=/dev/fb0

# Python path
export PYTHONPATH=/home/pi/RPIFrame:$PYTHONPATH

# Disable audio (optional, if no audio needed)
export SDL_AUDIODRIVER=dummy
```

### 2. Test Display Functionality

Before setting up the service, test that the display works:

```bash
cd /home/pi/RPIFrame
source venv/bin/activate
source .env

# Test basic display
python test_display.py

# If successful, test the full application
python main.py --display-only
```

If you see the test patterns, the display is working correctly.

## Systemd Service Setup

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/rpiframe.service
```

Add the following content:
```ini
[Unit]
Description=RPIFrame DSI Photo Frame
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=video
WorkingDirectory=/home/pi/RPIFrame

# Environment
Environment="PATH=/home/pi/RPIFrame/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="SDL_VIDEODRIVER=kmsdrm"
Environment="SDL_FBDEV=/dev/fb0"
Environment="PYTHONPATH=/home/pi/RPIFrame"
Environment="HOME=/home/pi"

# Start command
ExecStartPre=/bin/sleep 10
ExecStart=/home/pi/RPIFrame/venv/bin/python /home/pi/RPIFrame/main.py

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Logging
StandardOutput=append:/home/pi/RPIFrame/logs/rpiframe.log
StandardError=append:/home/pi/RPIFrame/logs/rpiframe-error.log

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable rpiframe.service

# Start service
sudo systemctl start rpiframe.service

# Check status
sudo systemctl status rpiframe.service
```

### 3. Service Management Commands

```bash
# View logs
sudo journalctl -u rpiframe.service -f

# View application logs
tail -f /home/pi/RPIFrame/logs/rpiframe.log

# Restart service
sudo systemctl restart rpiframe.service

# Stop service
sudo systemctl stop rpiframe.service

# Disable auto-start
sudo systemctl disable rpiframe.service
```

## Network Configuration

### 1. Firewall Rules (if using ufw)

```bash
# Allow web interface port
sudo ufw allow 5000/tcp

# Enable firewall
sudo ufw enable
```

### 2. Find Pi's IP Address

```bash
hostname -I
```

Access the web interface at: `http://[PI-IP-ADDRESS]:5000`

## Performance Optimization

### 1. Boot Time Optimization

```bash
# Disable unnecessary services for faster boot
sudo systemctl disable bluetooth.service
sudo systemctl disable avahi-daemon.service
sudo systemctl disable triggerhappy.service

# Only if not using WiFi:
# sudo systemctl disable wpa_supplicant.service
```

### 2. Memory Optimization

Add to `/boot/firmware/cmdline.txt` (all on one line):
```
cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory
```

### 3. Swap Configuration (for 2GB Pi 4)

```bash
# Increase swap size
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=512
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Troubleshooting

### Display Not Working

1. Check framebuffer device:
```bash
ls -la /dev/fb*
# Should show /dev/fb0 with video group access
```

2. Test framebuffer directly:
```bash
# Fill with random colors (Ctrl+C to stop)
cat /dev/urandom > /dev/fb0
```

3. Check KMS driver:
```bash
sudo vcdbg log msg
dmesg | grep -i drm
```

### Web Interface Not Accessible

1. Check if service is running:
```bash
sudo systemctl status rpiframe.service
```

2. Check if port is listening:
```bash
sudo netstat -tlnp | grep 5000
```

3. Check firewall:
```bash
sudo ufw status
```

### Touch Not Working

1. Check input devices:
```bash
ls -la /dev/input/
evtest  # Install with: sudo apt install evtest
```

2. Check touch events:
```bash
sudo evtest /dev/input/event0  # Try different event numbers
```

### Service Fails to Start

1. Check logs:
```bash
sudo journalctl -u rpiframe.service -n 50 --no-pager
cat /home/pi/RPIFrame/logs/rpiframe-error.log
```

2. Test manually:
```bash
cd /home/pi/RPIFrame
source venv/bin/activate
source .env
python main.py --debug
```

### Memory Issues

Monitor memory usage:
```bash
free -h
htop
```

If running out of memory:
- Reduce photo resolution before uploading
- Increase swap size
- Consider using Raspberry Pi 4 with 4GB or 8GB RAM

## Backup and Recovery

### Create Backup

```bash
# Backup photos
tar -czf rpiframe-photos-$(date +%Y%m%d).tar.gz /home/pi/RPIFrame/photos/

# Backup configuration
cp /home/pi/RPIFrame/config.json /home/pi/RPIFrame/config.json.backup

# Full SD card backup (from another computer)
sudo dd if=/dev/sdX of=rpiframe-backup.img bs=4M status=progress
```

### Restore from Backup

```bash
# Restore photos
tar -xzf rpiframe-photos-20240101.tar.gz -C /

# Restore config
cp /home/pi/RPIFrame/config.json.backup /home/pi/RPIFrame/config.json
```

## Security Considerations

### 1. Change Default Password

```bash
passwd
```

### 2. Disable Password Authentication (use SSH keys)

```bash
# Copy your public key to Pi first
ssh-copy-id pi@rpiframe.local

# Then disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### 3. Regular Updates

Create update script:
```bash
nano /home/pi/update-rpiframe.sh
```

Add:
```bash
#!/bin/bash
cd /home/pi/RPIFrame
source venv/bin/activate
git pull
pip install -r requirements.txt --upgrade
sudo systemctl restart rpiframe.service
```

Make executable:
```bash
chmod +x /home/pi/update-rpiframe.sh
```

## Monitoring

### 1. Simple Health Check Script

```bash
nano /home/pi/check-rpiframe.sh
```

Add:
```bash
#!/bin/bash
if systemctl is-active --quiet rpiframe.service; then
    echo "RPIFrame is running"
else
    echo "RPIFrame is NOT running"
    sudo systemctl start rpiframe.service
fi
```

### 2. Add to Crontab

```bash
crontab -e
```

Add:
```
# Check every 5 minutes
*/5 * * * * /home/pi/check-rpiframe.sh >> /home/pi/RPIFrame/logs/health-check.log 2>&1
```

## Final Notes

- The system will start automatically on boot
- Allow 30-60 seconds for full startup after power on
- Access web interface from any device on your network
- Upload photos via the web interface
- Photos will automatically display in slideshow
- Touch/swipe to manually navigate photos

For additional help, check the logs or refer to the main README.md file.