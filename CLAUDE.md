# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**RPIFrame** is a full-color digital photo frame application for Raspberry Pi 4 with Hosyond 7-inch DSI touchscreen. Originally adapted from the InkFrame project, it has been completely refactored with a modern, modular architecture.

## Current Status - REFACTORED 🚀

### Recent Major Refactor (December 2024)
The entire project has been refactored to address critical issues:

### Latest Updates (June 2025) - MAJOR IMPROVEMENTS ✨
- **✅ DISPLAY STRETCHING FIXED**: Resolved horizontal image stretching issue on DSI display
  - Implemented horizontal pre-squish compensation (0.9 factor) to counter hardware stretching
  - Completely rewrote image processing with proper 4-step algorithm:
    1. Center crop based on original image dimensions
    2. Apply counter-squish compensation 
    3. Scale to display size
    4. Final crop for exact fit
  - Images now display with correct aspect ratios and proper centering

- **✅ ENHANCED WEB INTERFACE**:
  - Added "Next Photo" button to Photos tab for easy testing
  - Current photo preview shows what's displaying on the physical frame
  - Removed redundant "Refresh Display" button
  - Real-time preview updates when advancing photos
  - Enhanced system monitoring with CPU/Memory usage bars (htop-style)

- **✅ IMPROVED SLIDESHOW FUNCTIONALITY**:
  - Random photo selection on startup (no longer always starts with first photo)
  - Fixed slideshow interval to respect web interface settings (15 minutes)
  - Web-triggered photo advancement via API signal system
  - Better centering algorithm prevents top/bottom cropping issues

- **✅ COMPREHENSIVE SYSTEM MONITORING**:
  - Tech stack information with version details
  - Health checks and recommendations system
  - Resource usage visualization with color-coded bars
  - Streamlined system information display

- **🎯 CURRENT STATUS**: All major display and interface issues resolved. Frame now displays photos with correct aspect ratios and provides excellent web-based management.

**✅ Complete Architecture Overhaul**
- Migrated from scattered files to clean Python package structure (`rpiframe/`)
- Unified configuration system replacing multiple conflicting configs
- Proper dependency management with graceful degradation
- Professional installation and setup scripts

**✅ New Project Structure**
```
RPIFrame/
├── rpiframe/              # Main Python package
│   ├── __init__.py       # Package initialization
│   ├── core.py           # Main orchestrator (PhotoFrame class)
│   ├── config.py         # Unified configuration management
│   ├── display.py        # Display manager with touch support
│   ├── web.py            # Flask web server and API
│   └── utils.py          # Common utilities
├── run.py                 # New clean entry point
├── setup.py              # Automated setup script
├── stop_all.py           # Process management utility
├── debug_photos.py       # Photo path debugging tool
├── requirements-new.txt   # Updated dependencies
├── README-new.md         # Updated documentation
└── [legacy files]        # Old implementation (to be removed)
```

**✅ Key Improvements**
- Fixed all import errors and module conflicts
- Added port conflict detection and handling
- Robust error handling with informative messages
- Proper absolute path handling for photos
- Clean process management and shutdown
- Comprehensive logging system

### Remaining Tasks
1. **HEIC support**: Add conversion for Apple photos on upload
2. **Transition effects**: Implement wipe/fade transitions between photos (framework ready)
3. **Photo organization**: Albums/folders support for better management
4. **Cloud integration**: Google Photos, iCloud sync capabilities

### Recently Resolved ✅
1. ~~**Display stretching**: Fixed with 0.9x horizontal pre-squish compensation~~
2. ~~**Photo centering**: Improved crop algorithm for proper subject positioning~~
3. ~~**Web interface**: Enhanced with current photo preview and Next Photo button~~
4. ~~**System monitoring**: Added comprehensive resource tracking and health checks~~
5. ~~**Configuration sync**: Fixed slideshow interval to respect web settings~~

## Architecture

### Core Components (Refactored)

#### `rpiframe/core.py` - PhotoFrame Class
- Main orchestrator managing web and display processes
- Process monitoring and restart capability
- Port conflict detection
- Platform detection (Pi vs development)

#### `rpiframe/config.py` - Config Class
- Centralized configuration management
- Automatic default generation
- Configuration validation
- Easy get/set methods

#### `rpiframe/display.py` - DisplayManager Class
- Pygame-based slideshow with touch support
- Advanced 4-step image processing with aspect ratio preservation
- Horizontal pre-squish compensation (0.9 factor) for display stretching
- EXIF rotation support and proper center cropping
- Multiple fit modes (contain/cover) with intelligent scaling
- Web-triggered photo advancement via signal files

#### `rpiframe/web.py` - WebServer Class
- Flask-based photo management API with slideshow control
- Current photo tracking and preview API endpoints
- Enhanced system monitoring with tech stack information
- Resource usage tracking (CPU, memory, storage) with health checks
- Fixed absolute path handling and thumbnail generation

#### `run.py` - Entry Point
- Clean command-line interface
- Options: --web-only, --display-only, --config
- Proper argument parsing

## After Reboot Instructions

Once you've rebooted the Pi, the DSI display should be properly initialized. To start RPIFrame:

1. **From local console** (keyboard attached to Pi):
   ```bash
   cd /home/spencer/RPIFrame
   python3 run.py
   ```

2. **For auto-start on boot**, create a systemd service:
   ```bash
   sudo nano /etc/systemd/system/rpiframe.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=RPIFrame Photo Display
   After=multi-user.target
   
   [Service]
   Type=simple
   User=spencer
   WorkingDirectory=/home/spencer/RPIFrame
   ExecStart=/usr/bin/python3 /home/spencer/RPIFrame/run.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Then enable:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable rpiframe.service
   sudo systemctl start rpiframe.service
   ```

## Key Commands

### Development/Testing
```bash
# Setup and install dependencies
python3 setup.py

# Run web interface only (safe for development)
python3 run.py --web-only

# Run full application (Pi only)
python3 run.py

# Stop all processes
python3 stop_all.py

# Debug photo paths
python3 debug_photos.py

# Run with custom config
python3 run.py --config custom.json
```

### Git Workflow
```bash
# Current status: refactored code is pushed to GitHub
# Latest commits:
# - c1ab616: Fix broken image paths in web interface
# - c8f66a5: Add port conflict detection and process management
# - a20f425: Complete RPIFrame refactor

# To sync on Raspberry Pi:
git pull origin main

# After making changes on Pi:
git add -A
git commit -m "Description of changes"
git push origin main
```

## Configuration

### Unified Configuration (`config.json`)
```json
{
  "display": {
    "width": 800,
    "height": 480,
    "rotation": 0,
    "slideshow_interval": 60,
    "fit_mode": "contain"
  },
  "photos": {
    "directory": "photos",
    "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "gif"],
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

## Recommended Development Workflow

### Moving Development to Raspberry Pi

1. **Install Claude Code on Pi**:
   ```bash
   # Install via snap or binary
   # Configure with API key
   ```

2. **Clone and setup on Pi**:
   ```bash
   git clone https://github.com/spenceriam/RPIFrame.git
   cd RPIFrame
   python3 setup.py
   ```

3. **Development cycle**:
   - Edit with Claude Code on Pi
   - Test immediately: `python3 run.py --web-only`
   - Commit and push changes
   - Full test: `python3 run.py`

### Benefits of Pi Development
- Immediate testing of display functionality
- Real hardware validation
- No cross-platform issues
- Faster iteration cycle
- Direct access to GPIO/hardware features

## Pending Features

### High Priority
1. **HEIC Support** - Convert Apple photos to JPEG on upload
2. **Better error recovery** - Auto-restart failed components
3. **Photo organization** - Albums/folders support
4. **Performance optimization** - Caching, lazy loading

### Medium Priority
1. **Transition effects** - Fade, slide animations
2. **Weather/clock overlay** - Optional info display
3. **Remote control** - Mobile app or web remote
4. **Backup/restore** - Configuration and photos

### Future Enhancements
1. **Multi-frame sync** - Control multiple frames
2. **Cloud integration** - Google Photos, iCloud
3. **Motion detection** - Turn on when someone nearby
4. **Schedule** - Different photos at different times

## Important Notes for Development

### Platform Differences
- **On Pi**: Full functionality with display and touch
- **On PC/Mac**: Web-only mode for development
- **Dependencies**: pygame optional on non-Pi systems

### Error Handling
- All modules handle missing dependencies gracefully
- Comprehensive logging to `logs/rpiframe.log`
- Clear error messages with suggested fixes

### Testing Checklist
- [ ] Web upload works
- [ ] Photos display correctly
- [ ] Touch navigation works (Pi only)
- [ ] Configuration changes persist
- [ ] Process management (stop/start)
- [ ] Port conflict handling

## Troubleshooting

### Common Issues

1. **Broken images in web interface**
   - Run `python3 debug_photos.py`
   - Check photos directory exists
   - Verify absolute paths

2. **Port already in use**
   - Run `python3 stop_all.py`
   - Check with `lsof -i :5000`
   - Change port in config.json

3. **Display not working / Black screen**
   - **Most common fix**: Reboot the Pi (SSH sessions can't directly access DSI display)
   - After reboot, run directly on Pi console or set up auto-start
   - Check `/boot/firmware/config.txt` for DSI display settings:
     ```
     display_auto_detect=1
     dtoverlay=vc4-kms-v3d
     ```
   - Application logs show it's working (photos advancing) but output not reaching screen
   - Consider creating systemd service for auto-start on boot:
     ```bash
     sudo systemctl enable rpiframe.service
     sudo systemctl start rpiframe.service
     ```

4. **Import errors**
   - Run `python3 setup.py`
   - Install missing dependencies
   - Check Python version (3.7+)

## Summary

The RPIFrame project has been completely refactored with:
- ✅ Clean, modular architecture
- ✅ Robust error handling
- ✅ Fixed import and path issues
- ✅ Professional Python package structure
- ✅ Comprehensive documentation

**Recommendation**: Move development to Raspberry Pi for faster iteration and real hardware testing. The refactored codebase is stable and ready for feature additions like HEIC support.