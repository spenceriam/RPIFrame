# RPIFrame: Full-Color DSI Photo Frame

A completely refactored, modern digital photo frame application for Raspberry Pi 4 with DSI touchscreen display. Features a professional web interface, enhanced image processing, and robust system architecture.

## 🚀 Recent Major Updates (June 2025)

- **✅ DISPLAY STRETCHING FIXED**: Resolved horizontal image stretching with 0.9x compensation
- **✅ ENHANCED WEB INTERFACE**: Added "Next Photo" button and real-time preview
- **✅ IMPROVED IMAGE PROCESSING**: 4-step algorithm with proper aspect ratio preservation
- **✅ COMPREHENSIVE REFACTOR**: Clean Python package structure with robust error handling

## Features

- 🖼️ **Full-Color Display**: Displays photos in vibrant full color on DSI touchscreen
- 🌐 **Web Interface**: Upload and manage photos from any device on your network
- 👆 **Touch Navigation**: Swipe left/right to navigate through photos
- 🔄 **Auto-Rotation**: Configurable slideshow with smooth transitions
- 📱 **Responsive Design**: Mobile-friendly web interface
- 🎨 **Image Rotation**: Control image orientation via web interface
- 💾 **Efficient Storage**: Automatic thumbnail generation for web gallery
- 🖥️ **Headless Operation**: Runs as a system service on boot

## Hardware Requirements

- **Raspberry Pi 4** (2GB RAM or higher recommended)
- **Hosyond 7-inch DSI IPS touchscreen** 
  - Resolution: 800×480 pixels
  - Touch: FT5426 capacitive controller (2-point touch)
  - Interface: MIPI DSI with RGB888
  - Power: 3.3V, 510mA max
  - Includes: FPC cables, mounting hardware
- **MicroSD Card** (16GB or larger recommended)
- **Power Supply** (5V 3A USB-C for Pi 4)
- **Optional**: Case or mounting solution

## Software Requirements

- **Raspberry Pi OS Lite** (64-bit, Bookworm or later)
- **Python 3.9+**
- **Network connection** (for web interface access)

## Installation

### 1. Prepare Raspberry Pi OS

First, install Raspberry Pi OS Lite (64-bit) on your SD card using Raspberry Pi Imager.

Boot your Raspberry Pi and ensure it's connected to your network.

### 2. Enable DSI Display

Edit the boot configuration:
```bash
sudo nano /boot/firmware/config.txt
```

Add or uncomment these lines:
```
# Enable DSI display
dtoverlay=vc4-kms-v3d
display_auto_detect=1
```

### 3. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and required system packages
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y git
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev
```

### 4. Clone and Setup RPIFrame

```bash
# Clone the repository
cd ~
git clone https://github.com/spenceriam/RPIFrame.git
cd RPIFrame

# Run automated setup (installs dependencies and creates config)
python3 setup.py
```

### 5. Configure RPIFrame

The application will create a default configuration on first run. You can also manually edit:

```bash
nano config.json
```

Default configuration:
```json
{
  "display": {
    "width": 800,
    "height": 480,
    "rotation": 0,
    "slideshow_interval": 900,
    "fit_mode": "contain"
  },
  "photos": {
    "directory": "photos",
    "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "gif", "heic", "heif"],
    "max_upload_size_mb": 50,
    "thumbnail_size": 200
  },
  "system": {
    "enable_touch": true,
    "debug_mode": false,
    "log_level": "INFO"
  },
  "web": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

### 6. Test the Application

```bash
# Test web interface only (safe for development)
python3 run.py --web-only

# Test display only (Pi with connected display)
python3 run.py --display-only

# Run full application (Pi only)
python3 run.py

# Stop all processes if needed
python3 stop_all.py
```

Access the web interface at `http://YOUR_PI_IP:5000`

## Usage

### Web Interface

1. **Access the Web Interface**: Open a browser and navigate to `http://YOUR_PI_IP:5000`
2. **Upload Photos**: 
   - Drag and drop photos onto the upload area
   - Or click to select files
   - Supports JPG, PNG, BMP, and GIF formats
3. **Manage Photos**:
   - View all uploaded photos in the gallery
   - Delete unwanted photos
   - Photos are automatically resized and optimized
4. **Configure Settings**:
   - Adjust slideshow interval (10 seconds to 1 hour)
   - Set display rotation (0°, 90°, 180°, 270°)
   - Enable/disable touch controls

### Touchscreen Controls

When touch is enabled:
- **Swipe Left**: Next photo
- **Swipe Right**: Previous photo
- **Automatic Advance**: Photos change based on configured interval

### Keyboard Controls (for testing)

When running with a keyboard attached:
- **Right Arrow**: Next photo
- **Left Arrow**: Previous photo
- **Escape**: Exit application

## Auto-Start on Boot

### Create Systemd Service

Create the service file:
```bash
sudo nano /etc/systemd/system/rpiframe.service
```

Add the following content:
```ini
[Unit]
Description=RPIFrame DSI Photo Frame
After=network.target

[Service]
Type=forking
User=spencer
WorkingDirectory=/home/spencer/RPIFrame
ExecStart=/usr/bin/python3 /home/spencer/RPIFrame/run.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable rpiframe.service

# Start the service
sudo systemctl start rpiframe.service

# Check status
sudo systemctl status rpiframe.service
```

### Service Management

```bash
# View logs
journalctl -u rpiframe.service -f

# Stop service
sudo systemctl stop rpiframe.service

# Restart service
sudo systemctl restart rpiframe.service

# Disable auto-start
sudo systemctl disable rpiframe.service
```

## Advanced Configuration

### Display Rotation

If your display is mounted in a non-standard orientation:

1. Via web interface: Settings → Display Rotation
2. Via config file: Edit `config.json` and set `display.rotation` to 0, 90, 180, or 270

### Network Configuration

To change the web server port:
```bash
python main.py --port 8080
```

Or edit `config.json`:
```json
{
  "system": {
    "web_port": 8080
  }
}
```

### Performance Tuning

For Raspberry Pi Zero W or older models:
- Increase slideshow interval to reduce CPU usage
- Disable transition effects
- Reduce photo resolution before uploading

## Troubleshooting

### Display Not Working / Black Screen

**Most common fix**: Reboot the Pi - SSH sessions can't directly access DSI display
```bash
sudo reboot
# After reboot, run directly on Pi console:
python3 run.py
```

Other fixes:
1. Check DSI cable connection
2. Verify `/boot/firmware/config.txt` settings:
   ```
   display_auto_detect=1
   dtoverlay=vc4-kms-v3d
   ```
3. Try web-only mode first: `python3 run.py --web-only`

### Web Interface Not Accessible

1. Check if port is in use: `python3 stop_all.py`
2. Get Pi's IP address: `hostname -I`
3. Check logs: `tail -f logs/rpiframe.log`
4. Debug photo paths: `python3 debug_photos.py`

### Import Errors / Dependencies

1. Run automated setup: `python3 setup.py`
2. Check Python version: `python3 --version` (3.7+ required)
3. Install missing deps manually: `pip3 install -r requirements-new.txt`

### Photos Not Displaying Correctly

1. **Image stretching**: Fixed in current version with 0.9x compensation
2. **Wrong aspect ratio**: Check `fit_mode` in config.json ("contain" or "cover")
3. **Photos not found**: Run `python3 debug_photos.py`
4. **Upload issues**: Check `max_upload_size_mb` and file extensions

### Process Management

```bash
# Stop all RPIFrame processes
python3 stop_all.py

# Check what's running on port 5000
lsof -i :5000

# Restart cleanly
python3 run.py
```

## Development

### Project Structure

```
RPIFrame/
├── rpiframe/            # Main Python package
│   ├── __init__.py      # Package initialization
│   ├── core.py          # PhotoFrame orchestrator
│   ├── config.py        # Configuration management
│   ├── display.py       # Display/slideshow manager
│   ├── web.py           # Flask web server and API
│   └── utils.py         # Common utilities
├── run.py               # New main entry point
├── setup.py             # Automated setup script
├── stop_all.py          # Process management utility
├── requirements-new.txt # Updated dependencies
├── config.json          # Configuration file (auto-created)
├── templates/           # HTML templates
│   └── index.html       # Enhanced web interface
├── static/              # CSS/JS assets
├── photos/              # Photo storage
├── logs/                # Application logs
└── README.md            # This documentation
```

### Running in Development Mode

```bash
# Run web interface only (safe for development on any system)
python3 run.py --web-only

# Run with verbose logging
python3 run.py --web-only --verbose

# Use custom configuration file
python3 run.py --config custom.json

# Debug photo paths and system status
python3 debug_photos.py
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on actual Raspberry Pi hardware
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- Adapted from the InkFrame project for e-ink displays
- Built with Flask, Pygame, and Pillow
- Designed for Raspberry Pi community

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

Made with ❤️ for Raspberry Pi enthusiasts