# RPIFrame Deployment Plan

This document outlines the complete deployment strategy for RPIFrame on Raspberry Pi 4 with Hosyond 7-inch DSI display.

## Deployment Options

### Option 1: Fresh Installation (Recommended)
For new Raspberry Pi setups or clean installations.

### Option 2: Existing Pi Update
For updating an existing RPIFrame installation.

### Option 3: Pre-configured Image
For deploying multiple units or production use.

---

## Option 1: Fresh Installation

### Prerequisites Checklist
- [ ] Raspberry Pi 4 (2GB+ RAM)
- [ ] Hosyond 7-inch DSI display with FPC cables
- [ ] MicroSD card (16GB+, Class 10 or better)
- [ ] Reliable internet connection
- [ ] SSH access configured
- [ ] Basic Linux/Pi knowledge

### Step 1: Hardware Assembly
1. **Mount the display** to Pi 4 using included copper standoffs
2. **Connect DSI cable** (use 5cm FPC cable, contacts facing down)
3. **Test power** - Ensure 5V 3A USB-C supply
4. **Initial boot** - Verify display shows boot sequence

### Step 2: Base OS Installation
```bash
# Flash Raspberry Pi OS Lite (64-bit) using Pi Imager
# Configure WiFi, SSH, user account during imaging

# First boot verification
ssh pi@rpiframe.local  # or use IP address
sudo apt update && sudo apt upgrade -y
```

### Step 3: RPIFrame Deployment
```bash
# Clone repository
cd /home/pi
git clone https://github.com/yourusername/RPIFrame.git
cd RPIFrame

# Run automated installation
chmod +x install.sh
./install.sh
```

### Step 4: Validation
```bash
# Test display functionality
python test_display.py

# Check service status
sudo systemctl status rpiframe.service

# Access web interface
# Open browser to http://[PI_IP]:5000
```

### Estimated Time: 45-60 minutes

---

## Option 2: Existing Pi Update

### For Existing RPIFrame Installations
```bash
# Stop service
sudo systemctl stop rpiframe.service

# Backup current configuration
cp /home/pi/RPIFrame/config.json /home/pi/config.json.backup
tar -czf /home/pi/photos-backup-$(date +%Y%m%d).tar.gz /home/pi/RPIFrame/photos/

# Update code
cd /home/pi/RPIFrame
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restore configuration
cp /home/pi/config.json.backup config.json

# Restart service
sudo systemctl daemon-reload
sudo systemctl start rpiframe.service
```

### For Converting from InkFrame
```bash
# Stop InkFrame service
sudo systemctl stop inkframe-display.service
sudo systemctl disable inkframe-display.service

# Backup photos and config
cp /home/pi/InkFrame/config.json /home/pi/inkframe-config.backup
tar -czf /home/pi/inkframe-photos-backup.tar.gz /home/pi/InkFrame/static/images/photos/

# Deploy RPIFrame (fresh installation)
cd /home/pi
git clone https://github.com/yourusername/RPIFrame.git
cd RPIFrame
./install.sh

# Migrate photos
cp -r /home/pi/InkFrame/static/images/photos/* /home/pi/RPIFrame/photos/

# Manual config migration may be needed due to different structure
```

---

## Option 3: Pre-configured Image

### Creating Master Image
```bash
# Complete fresh installation on reference Pi
# Configure and test thoroughly
# Clean up for imaging

# On reference Pi - cleanup before imaging
sudo apt clean
sudo apt autoremove -y
rm -rf /home/pi/.bash_history
rm -rf /home/pi/RPIFrame/logs/*
sudo dd if=/dev/zero of=/tmp/zero bs=1M || true
sudo rm /tmp/zero
sudo shutdown -h now

# Create image from another computer
sudo dd if=/dev/sdX of=rpiframe-v1.0.img bs=4M status=progress
gzip rpiframe-v1.0.img
```

### Deploying Pre-configured Image
```bash
# Flash image to new SD cards
gunzip -c rpiframe-v1.0.img.gz | sudo dd of=/dev/sdX bs=4M status=progress

# First boot configuration per unit
ssh pi@rpiframe.local
sudo raspi-config  # Change hostname, password, WiFi if needed
```

---

## Production Deployment Checklist

### Pre-deployment Validation
- [ ] Hardware connectivity test
- [ ] Display functionality verification
- [ ] Touch input testing
- [ ] Network connectivity
- [ ] Service auto-start verification
- [ ] Web interface accessibility
- [ ] Photo upload/display testing

### Security Hardening
```bash
# Change default password
passwd

# Disable password authentication (use SSH keys)
ssh-copy-id pi@rpiframe.local
# Then edit /etc/ssh/sshd_config: PasswordAuthentication no

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 5000/tcp

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
```

### Monitoring Setup
```bash
# Create health check script
cat > /home/pi/health-check.sh << 'EOF'
#!/bin/bash
LOG="/home/pi/RPIFrame/logs/health.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

if systemctl is-active --quiet rpiframe.service; then
    echo "$DATE - RPIFrame service is running" >> $LOG
else
    echo "$DATE - ERROR: RPIFrame service is DOWN" >> $LOG
    sudo systemctl start rpiframe.service
fi

# Check disk space
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $USAGE -gt 90 ]; then
    echo "$DATE - WARNING: Disk usage is ${USAGE}%" >> $LOG
fi
EOF

chmod +x /home/pi/health-check.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/pi/health-check.sh") | crontab -
```

---

## Troubleshooting Quick Reference

### Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Display not working | Check FPC cable, verify config.txt |
| Touch not responding | Check `/dev/input/event*`, test with `evtest` |
| Service won't start | Check logs: `journalctl -u rpiframe.service` |
| Web interface down | Verify port 5000: `netstat -tlnp \| grep 5000` |
| Photos not uploading | Check disk space, permissions on `/photos` |

### Log Locations
- **Service logs**: `journalctl -u rpiframe.service -f`
- **Application logs**: `/home/pi/RPIFrame/logs/rpiframe.log`
- **Error logs**: `/home/pi/RPIFrame/logs/rpiframe-error.log`
- **Health logs**: `/home/pi/RPIFrame/logs/health.log`

---

## Rollback Plan

### Quick Rollback
```bash
# Stop new service
sudo systemctl stop rpiframe.service

# Restore from backup
tar -xzf /home/pi/photos-backup-YYYYMMDD.tar.gz -C /
cp /home/pi/config.json.backup /home/pi/RPIFrame/config.json

# Restart service
sudo systemctl start rpiframe.service
```

### Full Rollback to Previous Version
```bash
cd /home/pi/RPIFrame
git log --oneline  # Find previous commit
git checkout <previous-commit-hash>
sudo systemctl restart rpiframe.service
```

---

## Update Strategy

### Regular Updates
```bash
#!/bin/bash
# /home/pi/update-rpiframe.sh

cd /home/pi/RPIFrame
sudo systemctl stop rpiframe.service

# Backup
cp config.json config.json.backup.$(date +%Y%m%d)

# Update
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart
sudo systemctl start rpiframe.service

# Verify
sleep 10
systemctl is-active rpiframe.service && echo "Update successful" || echo "Update failed"
```

### Scheduled Updates (Optional)
```bash
# Add to crontab for weekly updates
0 2 * * 0 /home/pi/update-rpiframe.sh >> /home/pi/RPIFrame/logs/update.log 2>&1
```

---

## Deployment Timeline

### Single Unit: ~1 hour
- Hardware assembly: 10 minutes
- OS installation: 15 minutes
- RPIFrame deployment: 20 minutes
- Testing and validation: 15 minutes

### Multiple Units (with master image): ~15 minutes each
- Image flashing: 5 minutes
- Basic configuration: 5 minutes
- Validation: 5 minutes

---

## Support and Maintenance

### Regular Maintenance Tasks
- **Weekly**: Check logs for errors
- **Monthly**: Update system packages
- **Quarterly**: Full backup and update RPIFrame
- **As needed**: Photo cleanup, storage management

### Getting Help
1. Check logs first
2. Review troubleshooting section
3. Test with `python test_display.py`
4. Check GitHub issues
5. Review deployment.md for detailed steps

---

## Summary

**Recommended approach for most users**: Option 1 (Fresh Installation)
- Simplest and most reliable
- Automated via install.sh
- Complete validation included

**For production/multiple units**: Option 3 (Pre-configured Image)
- Faster deployment at scale
- Consistent configuration
- Reduced chance of user error

The install.sh script handles 90% of the complexity, making deployment straightforward while still providing flexibility for advanced configurations.