# RPIFrame Validation Checklist

Quick verification steps to ensure your RPIFrame is working correctly after deployment.

## 🔧 Hardware Validation

### 1. Display Test
```bash
# Test display output
cd /home/pi/RPIFrame
python test_display.py
```
**Expected**: Color patterns appear on screen, touch advances patterns
**❌ If fails**: Check DSI cable connection, verify config.txt

### 2. Touch Test
```bash
# Check touch input devices
ls -la /dev/input/event*
# Should show event0, event1, etc.

# Test touch events (optional)
sudo evtest /dev/input/event0
# Touch screen - should show coordinate data
```
**Expected**: Touch coordinates appear when touching screen
**❌ If fails**: Touch controller not detected, check hardware connection

### 3. System Resources
```bash
# Check memory
free -h
# Should have >1GB available on 2GB Pi

# Check disk space
df -h
# Root partition should have >2GB free

# Check temperature
vcgencmd measure_temp
# Should be <70°C under normal load
```

## 🐍 Software Validation

### 4. Python Environment
```bash
cd /home/pi/RPIFrame
source venv/bin/activate

# Test dependencies
python -c "import pygame; print('Pygame OK')"
python -c "import flask; print('Flask OK')"
python -c "import PIL; print('Pillow OK')"
```
**Expected**: All imports succeed without errors

### 5. Configuration Loading
```bash
# Check config exists and is valid JSON
python -c "import json; print(json.load(open('config.json')))"
```
**Expected**: Prints configuration without errors

## 🖥️ Service Validation

### 6. Service Status
```bash
# Check service is running
sudo systemctl status rpiframe.service
```
**Expected**: 
- Status: `active (running)`
- No error messages in recent logs

### 7. Process Check
```bash
# Verify processes are running
ps aux | grep python
```
**Expected**: Should see both web server and display processes

### 8. Port Check
```bash
# Verify web server is listening
sudo netstat -tlnp | grep 5000
```
**Expected**: `0.0.0.0:5000` showing LISTEN state

## 🌐 Network Validation

### 9. Get IP Address
```bash
hostname -I
```
**Expected**: Shows Pi's IP address (e.g., 192.168.1.100)

### 10. Web Interface Access
From any device on your network, open browser to:
```
http://[PI_IP_ADDRESS]:5000
```
**Expected**: RPIFrame web interface loads
**❌ If fails**: Check firewall, service status

### 11. Basic Web Functions
In the web interface:
- **Upload test**: Try uploading a photo
- **Photo display**: Should appear in gallery
- **Settings**: Try changing slideshow interval
- **System status**: Should show service running

## 📸 Photo Display Validation

### 12. Photo Directory
```bash
ls -la /home/pi/RPIFrame/photos/
ls -la /home/pi/RPIFrame/photos/thumbnails/
```
**Expected**: Photos directory exists and is writable

### 13. Display Slideshow
**Manual test**:
1. Upload a photo via web interface
2. Wait for slideshow interval OR touch screen to advance
3. Photo should display fullscreen

**Expected**: Photo appears on display, touch navigation works

### 14. Log Check
```bash
# Check for errors in logs
tail -n 50 /home/pi/RPIFrame/logs/rpiframe.log
tail -n 50 /home/pi/RPIFrame/logs/rpiframe-error.log
```
**Expected**: No critical errors, normal startup messages

## 🔄 Auto-start Validation

### 15. Service Auto-start
```bash
# Check service is enabled for boot
sudo systemctl is-enabled rpiframe.service
```
**Expected**: Returns `enabled`

### 16. Reboot Test
```bash
# Test auto-start (optional but recommended)
sudo reboot

# After reboot, check service started automatically
sudo systemctl status rpiframe.service
```
**Expected**: Service starts automatically after reboot

## ⚡ Quick Validation Script

Save this as `/home/pi/validate.sh`:

```bash
#!/bin/bash
echo "🔍 RPIFrame Validation"
echo "====================="

# Service check
if systemctl is-active --quiet rpiframe.service; then
    echo "✅ Service is running"
else
    echo "❌ Service is NOT running"
fi

# Web server check
if netstat -tln | grep -q ":5000 "; then
    echo "✅ Web server is listening on port 5000"
else
    echo "❌ Web server is NOT listening"
fi

# Display check
if [ -c /dev/fb0 ]; then
    echo "✅ Framebuffer device available"
else
    echo "❌ Framebuffer device missing"
fi

# Touch check
if ls /dev/input/event* >/dev/null 2>&1; then
    echo "✅ Input devices detected"
else
    echo "❌ No input devices found"
fi

# Photos directory
if [ -w /home/pi/RPIFrame/photos ]; then
    echo "✅ Photos directory is writable"
else
    echo "❌ Photos directory is not writable"
fi

# Memory check
FREE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
if [ $FREE_MEM -gt 500 ]; then
    echo "✅ Memory: ${FREE_MEM}MB available"
else
    echo "⚠️  Memory: Only ${FREE_MEM}MB available"
fi

# Get IP for web access
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "🌐 Access web interface at: http://$IP:5000"
echo ""
echo "📋 Status Summary:"
echo "   Service: $(systemctl is-active rpiframe.service)"
echo "   Memory: ${FREE_MEM}MB free"
echo "   Photos: $(ls /home/pi/RPIFrame/photos/*.* 2>/dev/null | wc -l) files"
```

Make it executable and run:
```bash
chmod +x /home/pi/validate.sh
./validate.sh
```

## 🚨 Common Issues Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Display black | `sudo systemctl restart rpiframe.service` |
| Touch not working | Check `ls /dev/input/event*` |
| Web interface down | Check `sudo systemctl status rpiframe.service` |
| Photos not uploading | Check disk space: `df -h` |
| Service won't start | Check logs: `journalctl -u rpiframe.service` |

## ✅ Success Criteria

Your RPIFrame is working correctly if:
- ✅ Service status shows "active (running)"
- ✅ Web interface loads at http://[PI_IP]:5000
- ✅ Display shows content (test patterns or photos)
- ✅ Touch advances photos or shows coordinates
- ✅ Photo upload works via web interface
- ✅ Uploaded photos display in slideshow
- ✅ No critical errors in logs

**Time to validate**: ~5-10 minutes

If all validations pass, your RPIFrame is ready for use!