# RPIFrame 2.0 - Digital Photo Frame

A completely refactored, clean, and modern digital photo frame application for Raspberry Pi with DSI touchscreen displays.

## 🚀 Quick Start

### Installation

1. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd RPIFrame
   python3 setup.py
   ```

2. **Run web interface only (for testing):**
   ```bash
   python3 run.py --web-only
   ```

3. **Run full application (on Raspberry Pi):**
   ```bash
   python3 run.py
   ```

### Web Interface

Open your browser to `http://localhost:5000` to:
- Upload photos
- Manage photo collection
- Configure settings
- Monitor system status

## 📁 Project Structure

```
RPIFrame/
├── rpiframe/           # Main application package
│   ├── __init__.py     # Package initialization
│   ├── core.py         # Main PhotoFrame orchestrator
│   ├── config.py       # Configuration management
│   ├── display.py      # Display/slideshow manager
│   ├── web.py          # Web server and API
│   └── utils.py        # Utility functions
├── run.py              # Main entry point
├── setup.py            # Installation script
├── requirements-new.txt # Dependencies
├── config.json         # Configuration (created on first run)
├── photos/             # Photo storage
├── templates/          # Web interface templates
├── static/             # CSS/JS assets
└── logs/               # Application logs
```

## 🔧 Configuration

Configuration is managed through `config.json`:

```json
{
  "display": {
    "width": 800,
    "height": 480,
    "slideshow_interval": 60,
    "fit_mode": "contain"
  },
  "photos": {
    "directory": "photos",
    "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "gif"],
    "max_upload_size_mb": 50
  },
  "system": {
    "enable_touch": true,
    "log_level": "INFO"
  },
  "web": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

## 🖥️ Usage

### Command Line Options

```bash
python3 run.py [OPTIONS]

Options:
  --web-only        Run only web interface (no display)
  --display-only    Run only display slideshow (no web)
  --config FILE     Use custom config file
  --verbose, -v     Enable verbose logging
  --help           Show help message
```

### Examples

```bash
# Development mode (web only)
python3 run.py --web-only --verbose

# Production mode (full application)
python3 run.py

# Custom configuration
python3 run.py --config /path/to/custom.json

# Display only (no web interface)
python3 run.py --display-only
```

## 🔌 Hardware Support

- **Primary**: Raspberry Pi 4 with Hosyond 7-inch DSI touchscreen (800x480)
- **Compatible**: Any Raspberry Pi with DSI display support
- **Touch**: FT5426 capacitive touch controller

### Display Configuration

For Raspberry Pi OS, add to `/boot/firmware/config.txt`:
```ini
dtoverlay=vc4-fkms-v3d
display_auto_detect=1
gpu_mem=128
```

## 🌐 Web API

### Endpoints

- `GET /api/photos` - List all photos
- `POST /api/photos` - Upload photo
- `DELETE /api/photos/<id>` - Delete photo
- `POST /api/photos/<id>/rotate` - Rotate photo
- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration
- `GET /api/system/status` - System status

### Upload Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/photos', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🔧 Development

### Dependencies

Core dependencies:
- `Flask` - Web framework
- `Pillow` - Image processing
- `pygame` - Display management (Pi only)
- `psutil` - System monitoring

### Installing Dependencies

```bash
# Basic dependencies (development)
pip3 install Flask Pillow psutil

# Full dependencies (production)
pip3 install -r requirements-new.txt

# Or use setup script
python3 setup.py
```

### Testing

```bash
# Test web interface
python3 run.py --web-only

# Test display (Pi only)
python3 run.py --display-only

# Test configuration loading
python3 -c "from rpiframe import Config; c = Config(); print(c.to_dict())"
```

## 🚀 Deployment

### Automatic Service Setup

```bash
# Install and setup systemd service
python3 setup.py --systemd

# Enable auto-start
sudo systemctl enable rpiframe

# Start service
sudo systemctl start rpiframe

# Check status
sudo systemctl status rpiframe
```

### Manual Service

Create `/etc/systemd/system/rpiframe.service`:
```ini
[Unit]
Description=RPIFrame Digital Photo Frame
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/RPIFrame
ExecStart=/usr/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🎮 Touch Controls

- **Swipe Left**: Next photo
- **Swipe Right**: Previous photo
- **Keyboard**: Arrow keys for navigation, ESC to exit

## 📊 Features

### Core Features
- ✅ Clean, modular architecture
- ✅ Robust error handling
- ✅ Comprehensive logging
- ✅ Configuration management
- ✅ Web-based photo management
- ✅ Touch gesture navigation
- ✅ Automatic thumbnail generation
- ✅ System monitoring
- ✅ Multiple image formats
- ✅ Auto-rotation from EXIF
- ✅ Configurable slideshow timing

### Improvements from Original
- 🔄 Complete refactor with proper Python packaging
- 🛡️ Better error handling and graceful degradation
- 📱 Responsive web interface
- ⚙️ Centralized configuration system
- 🔍 Enhanced logging and monitoring
- 🚀 Simplified installation and deployment
- 🧪 Better separation of concerns
- 📦 Modular, importable design

## 🐛 Troubleshooting

### Common Issues

1. **Dependencies not found**
   ```bash
   python3 setup.py  # Install dependencies
   ```

2. **Display not working**
   ```bash
   python3 run.py --web-only  # Test without display
   ```

3. **Permission errors**
   ```bash
   sudo chown -R pi:pi /path/to/RPIFrame
   ```

4. **Service not starting**
   ```bash
   sudo journalctl -u rpiframe.service -f
   ```

### Logs

- Application logs: `logs/rpiframe.log`
- System logs: `sudo journalctl -u rpiframe.service`
- Web access: Browser developer console

## 📄 License

This project is open source. See original InkFrame project for licensing terms.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request

## 📞 Support

- Check logs first: `logs/rpiframe.log`
- Verify configuration: `python3 -c "from rpiframe import Config; Config().validate()"`
- Test components individually: `python3 run.py --web-only`