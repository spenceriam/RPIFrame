#!/bin/bash
#
# RPIFrame Installation Script
# For Raspberry Pi 4 with DSI touchscreen running Pi OS Lite (64-bit)
#
# This script automates the installation process for RPIFrame
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/home/$USER/RPIFrame"
SERVICE_NAME="rpiframe.service"
CURRENT_DIR=$(pwd)

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

troubleshoot_display() {
    print_header "Display Troubleshooting Information"
    
    echo "Collecting system information..."
    echo
    
    # Check kernel modules
    print_info "Video/DRM kernel modules:"
    lsmod | grep -E "(drm|vc4|v3d)" || echo "No DRM modules loaded"
    echo
    
    # Check display detection
    print_info "Display detection:"
    if [ -d /sys/class/drm ]; then
        ls -la /sys/class/drm/
    else
        echo "No DRM subsystem found"
    fi
    echo
    
    # Check for DSI in dmesg
    print_info "DSI-related kernel messages:"
    dmesg | grep -i dsi | tail -10 || echo "No DSI messages found"
    echo
    
    # Check current config
    print_info "Current display configuration:"
    if [ -f /boot/firmware/config.txt ]; then
        grep -E "(dtoverlay|display|gpu_mem|hdmi)" /boot/firmware/config.txt | grep -v "^#"
    elif [ -f /boot/config.txt ]; then
        grep -E "(dtoverlay|display|gpu_mem|hdmi)" /boot/config.txt | grep -v "^#"
    fi
    echo
    
    # Check permissions
    print_info "User groups:"
    groups $USER
    echo
}

check_raspberry_pi() {
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model)
        if [[ $MODEL == *"Raspberry Pi"* ]]; then
            print_success "Running on Raspberry Pi: $MODEL"
            return 0
        fi
    fi
    print_error "Not running on Raspberry Pi!"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

check_os_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_info "OS: $PRETTY_NAME"
        if [[ $ID == "raspbian" ]] || [[ $ID == "debian" ]]; then
            return 0
        fi
    fi
    print_error "Unsupported OS detected!"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

update_system() {
    print_header "Updating System Packages"
    sudo apt update
    sudo apt upgrade -y
    print_success "System updated"
}

install_system_dependencies() {
    print_header "Installing System Dependencies"
    
    # Core dependencies
    print_info "Installing Python and build tools..."
    sudo apt install -y python3-pip python3-venv python3-dev
    sudo apt install -y git build-essential
    
    # SDL2 libraries for Pygame
    print_info "Installing SDL2 libraries..."
    sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
    sudo apt install -y libfreetype6-dev libportmidi-dev libjpeg-dev zlib1g-dev libpng-dev
    
    # Additional libraries for headless operation
    print_info "Installing libraries for headless operation..."
    sudo apt install -y libgbm-dev libdrm-dev libgles2-mesa-dev
    sudo apt install -y libatlas-base-dev
    
    # Optional but useful tools
    print_info "Installing system tools..."
    sudo apt install -y htop iotop evtest
    
    print_success "System dependencies installed"
}

configure_display() {
    print_header "Configuring DSI Display"
    
    # Backup existing config
    if [ -f /boot/firmware/config.txt ]; then
        CONFIG_FILE="/boot/firmware/config.txt"
    elif [ -f /boot/config.txt ]; then
        CONFIG_FILE="/boot/config.txt"
    else
        print_error "Could not find boot config file!"
        return 1
    fi
    
    sudo cp $CONFIG_FILE ${CONFIG_FILE}.backup.$(date +%Y%m%d-%H%M%S)
    print_info "Backed up $CONFIG_FILE"
    
    # Remove conflicting display overlays first
    print_info "Checking for conflicting display overlays..."
    sudo sed -i 's/^dtoverlay=vc4-fkms-v3d/#dtoverlay=vc4-fkms-v3d/g' $CONFIG_FILE
    sudo sed -i 's/^dtoverlay=vc4-kms-v3d/#dtoverlay=vc4-kms-v3d/g' $CONFIG_FILE
    
    # Check if KMS driver is already configured
    if grep -q "^dtoverlay=vc4-kms-v3d" $CONFIG_FILE; then
        print_info "Display already configured with KMS driver"
    else
        print_info "Adding display configuration for Hosyond 7-inch DSI..."
        
        # Add new configuration
        sudo bash -c "cat >> $CONFIG_FILE << EOF

# RPIFrame Display Configuration for Hosyond 7-inch DSI
# Display: 800x480, FT5426 touch controller, MIPI DSI interface
# Using KMS driver for better DSI support
dtoverlay=vc4-kms-v3d
display_auto_detect=1
hdmi_force_hotplug=0
gpu_mem=128

# DSI display specific settings
ignore_lcd=0
disable_touchscreen=0

# Optional: PWM backlight control (uncomment if hardware modified)
# gpio=18=op,pu
EOF"
        print_success "Display configuration added for Hosyond 7-inch DSI"
        REBOOT_REQUIRED=true
    fi
    
    # Configure modules
    if ! grep -q "i2c-dev" /etc/modules; then
        echo "i2c-dev" | sudo tee -a /etc/modules > /dev/null
        print_success "Added i2c-dev module"
    fi
    
    # Check DSI display detection
    print_info "Checking for DSI display..."
    if ls /sys/class/drm/card*-DSI-* 2>/dev/null; then
        print_success "DSI display interface detected"
    else
        print_info "DSI display not detected yet (will check after reboot)"
    fi
}

configure_framebuffer() {
    print_header "Configuring Framebuffer Access"
    
    # Add user to video group
    sudo usermod -a -G video $USER
    print_success "Added $USER to video group"
    
    # Create udev rule
    sudo bash -c 'echo "KERNEL==\"fb*\", GROUP=\"video\", MODE=\"0660\"" > /etc/udev/rules.d/99-framebuffer.rules'
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    print_success "Framebuffer permissions configured"
}

setup_rpiframe() {
    print_header "Setting up RPIFrame"
    
    # Check if we're in the RPIFrame directory
    if [ -f "$CURRENT_DIR/main.py" ] && [ -f "$CURRENT_DIR/requirements.txt" ]; then
        print_info "Installing from current directory: $CURRENT_DIR"
        INSTALL_DIR="$CURRENT_DIR"
    else
        print_error "Not in RPIFrame directory!"
        print_info "Please run this script from the RPIFrame root directory"
        exit 1
    fi
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip wheel setuptools
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # If pygame fails, try alternative installation
    if ! python -c "import pygame" 2>/dev/null; then
        print_info "Pygame not found, trying alternative installation..."
        pip install --upgrade pygame --no-binary pygame
    fi
    
    print_success "Python dependencies installed"
    
    # Create required directories
    mkdir -p photos/thumbnails
    mkdir -p logs
    chmod 755 photos photos/thumbnails
    print_success "Created required directories"
    
    # Make scripts executable
    chmod +x main.py app.py display_slideshow.py test_display.py
    print_success "Made scripts executable"
    
    # Create environment file
    cat > $INSTALL_DIR/.env << EOF
# SDL settings for framebuffer
export SDL_VIDEODRIVER=kmsdrm
export SDL_FBDEV=/dev/fb0

# Python path
export PYTHONPATH=$INSTALL_DIR:\$PYTHONPATH

# Disable audio (optional)
export SDL_AUDIODRIVER=dummy
EOF
    print_success "Created environment file"
}

test_display() {
    print_header "Testing Display"
    
    # Check for display devices first
    print_info "Checking display devices..."
    if ls /dev/dri/card* 2>/dev/null; then
        print_success "DRM devices found:"
        ls -la /dev/dri/card*
    else
        print_error "No DRM devices found!"
        print_info "Display driver may not be loaded properly"
    fi
    
    # Check for framebuffer
    if ls /dev/fb* 2>/dev/null; then
        print_success "Framebuffer devices found:"
        ls -la /dev/fb*
    else
        print_error "No framebuffer devices found!"
    fi
    
    # Try different SDL drivers
    print_info "Testing SDL video drivers..."
    
    cd $INSTALL_DIR
    source venv/bin/activate
    
    # Test with KMS driver first (preferred for DSI)
    print_info "Testing with KMS/DRM driver..."
    export SDL_VIDEODRIVER=kmsdrm
    timeout 10s python test_display.py 2>/dev/null || true
    
    read -p "Did you see the test with KMS driver? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_success "KMS/DRM driver works!"
        echo "SDL_VIDEODRIVER=kmsdrm" > $INSTALL_DIR/.env
        return 0
    fi
    
    # Try with framebuffer driver
    print_info "Testing with framebuffer driver..."
    export SDL_VIDEODRIVER=fbdev
    export SDL_FBDEV=/dev/fb0
    timeout 10s python test_display.py 2>/dev/null || true
    
    read -p "Did you see the test with framebuffer driver? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_success "Framebuffer driver works!"
        cat > $INSTALL_DIR/.env << EOF
SDL_VIDEODRIVER=fbdev
SDL_FBDEV=/dev/fb0
EOF
        return 0
    fi
    
    # Display didn't work
    print_error "Display test failed with all drivers"
    print_info "Troubleshooting steps:"
    echo "1. Check DSI cable connection (contacts facing down)"
    echo "2. Verify display is powered properly"
    echo "3. Run: dmesg | grep -i dsi"
    echo "4. Check /boot/firmware/config.txt settings"
    echo "5. Try rebooting if display config was just changed"
    
    return 1
}

create_systemd_service() {
    print_header "Creating Systemd Service"
    
    # Create service file
    sudo tee /etc/systemd/system/$SERVICE_NAME > /dev/null << EOF
[Unit]
Description=RPIFrame DSI Photo Frame
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=video
WorkingDirectory=$INSTALL_DIR

# Environment
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="SDL_VIDEODRIVER=kmsdrm"
Environment="SDL_FBDEV=/dev/fb0"
Environment="PYTHONPATH=$INSTALL_DIR"
Environment="HOME=/home/$USER"

# Start command
ExecStartPre=/bin/sleep 10
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Logging
StandardOutput=append:$INSTALL_DIR/logs/rpiframe.log
StandardError=append:$INSTALL_DIR/logs/rpiframe-error.log

[Install]
WantedBy=multi-user.target
EOF

    print_success "Service file created"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable $SERVICE_NAME
    print_success "Service enabled for auto-start"
}

configure_firewall() {
    print_header "Configuring Firewall"
    
    # Check if ufw is installed
    if command -v ufw &> /dev/null; then
        sudo ufw allow 5000/tcp
        print_success "Firewall rule added for port 5000"
    else
        print_info "ufw not installed, skipping firewall configuration"
    fi
}

performance_optimization() {
    print_header "Applying Performance Optimizations"
    
    read -p "Apply performance optimizations? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping performance optimizations"
        return
    fi
    
    # Disable unnecessary services
    print_info "Disabling unnecessary services..."
    sudo systemctl disable bluetooth.service 2>/dev/null || true
    sudo systemctl disable avahi-daemon.service 2>/dev/null || true
    sudo systemctl disable triggerhappy.service 2>/dev/null || true
    
    # Configure swap (for 2GB models)
    if [ -f /etc/dphys-swapfile ]; then
        print_info "Configuring swap..."
        sudo dphys-swapfile swapoff
        sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=512/' /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
        print_success "Swap configured to 512MB"
    fi
    
    print_success "Performance optimizations applied"
}

print_summary() {
    print_header "Installation Complete!"
    
    echo
    echo "RPIFrame has been successfully installed!"
    echo
    echo "Important information:"
    echo "---------------------"
    echo "Installation directory: $INSTALL_DIR"
    echo "Service name: $SERVICE_NAME"
    echo "Web interface port: 5000"
    echo
    
    # Get IP address
    IP_ADDR=$(hostname -I | awk '{print $1}')
    if [ ! -z "$IP_ADDR" ]; then
        echo "Access the web interface at:"
        echo "http://$IP_ADDR:5000"
    fi
    
    echo
    echo "Useful commands:"
    echo "---------------"
    echo "Start service:   sudo systemctl start $SERVICE_NAME"
    echo "Stop service:    sudo systemctl stop $SERVICE_NAME"
    echo "View logs:       sudo journalctl -u $SERVICE_NAME -f"
    echo "Service status:  sudo systemctl status $SERVICE_NAME"
    echo
    
    if [ "$REBOOT_REQUIRED" = true ]; then
        echo -e "${YELLOW}IMPORTANT: A reboot is required for display configuration changes${NC}"
        echo
    fi
}

# Main installation flow
main() {
    clear
    print_header "RPIFrame Installation Script"
    echo "This script will install RPIFrame on your Raspberry Pi"
    echo "For Raspberry Pi OS Lite (64-bit) with DSI touchscreen"
    echo
    
    read -p "Continue with installation? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
    
    # Check system
    check_raspberry_pi
    check_os_version
    
    # Installation steps
    update_system
    install_system_dependencies
    configure_display
    configure_framebuffer
    setup_rpiframe
    
    # Test display
    read -p "Test display now? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        if ! test_display; then
            # Display test failed, offer troubleshooting
            read -p "Run display troubleshooting? (Y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                troubleshoot_display
            fi
        fi
    fi
    
    # Setup service
    create_systemd_service
    configure_firewall
    performance_optimization
    
    # Complete
    print_summary
    
    # Ask about starting service
    read -p "Start RPIFrame service now? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        sudo systemctl start $SERVICE_NAME
        print_success "RPIFrame service started"
    fi
    
    if [ "$REBOOT_REQUIRED" = true ]; then
        read -p "Reboot now? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            print_info "Rebooting..."
            sudo reboot
        fi
    fi
}

# Run main function
main