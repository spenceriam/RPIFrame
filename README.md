# RPIFrame: Full-Color DSI Photo Frame

A modern, full-color digital photo frame application for Raspberry Pi 4 with DSI touchscreen display. Features a web interface for photo management and touchscreen swipe navigation.

![RPIFrame Preview](docs/images/preview.png)

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
git clone https://github.com/yourusername/RPIFrame.git
cd RPIFrame

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
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
    "slideshow_interval": 60,
    "transition_effect": "fade"
  },
  "photos": {
    "directory": "photos",
    "allowed_extensions": ["png", "jpg", "jpeg", "gif", "bmp"],
    "max_upload_size_mb": 50
  },
  "system": {
    "web_port": 5000,
    "debug_mode": false,
    "enable_touch": true
  }
}
```

### 6. Test the Application

```bash
# Test web interface only
python main.py --web-only

# Test display only
python main.py --display-only

# Run both (full application)
python main.py
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
User=pi
WorkingDirectory=/home/pi/RPIFrame
Environment="PATH=/home/pi/RPIFrame/venv/bin"
ExecStart=/home/pi/RPIFrame/venv/bin/python /home/pi/RPIFrame/main.py
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

### Display Not Working

1. Check DSI cable connection
2. Verify `/boot/firmware/config.txt` settings
3. Try running with `--no-display` flag to test web interface only
4. Check logs: `journalctl -u rpiframe.service -n 100`

### Web Interface Not Accessible

1. Check Pi's IP address: `hostname -I`
2. Ensure firewall allows port 5000: `sudo ufw allow 5000`
3. Verify service is running: `systemctl status rpiframe.service`

### Photos Not Displaying

1. Check photo format (JPG, PNG, BMP, GIF supported)
2. Verify photos directory exists and has write permissions
3. Check available disk space: `df -h`
4. Review logs for errors

### Touch Not Working

1. Ensure touch is enabled in configuration
2. Check touchscreen driver: `ls /dev/input/event*`
3. Test touch with: `evtest` (install with `sudo apt install evtest`)

## Development

### Project Structure

```
RPIFrame/
├── main.py              # Main entry point
├── app.py               # Flask web application
├── display_slideshow.py # Display management
├── config.json          # Configuration file
├── requirements.txt     # Python dependencies
├── templates/           # HTML templates
│   └── index.html      # Web interface
├── static/             # Static assets (created on first run)
├── photos/             # Photo storage (created on first run)
│   └── thumbnails/     # Generated thumbnails
└── README.md           # This file
```

### Running in Development Mode

```bash
# Enable debug mode
python main.py --debug

# Run web interface only (for development on non-Pi systems)
python main.py --web-only --debug

# Disable display output (useful for testing on non-Pi systems)
python main.py --no-display
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