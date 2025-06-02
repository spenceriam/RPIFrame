#!/bin/bash
#
# Fix display issues for RPIFrame on Raspberry Pi with DSI display
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_header "RPIFrame Display Fix Script"

# 1. Check and install SDL2 libraries
print_header "Installing SDL2 Libraries"
print_info "Installing required SDL2 packages..."
sudo apt update
sudo apt install -y \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-ttf-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-gfx-1.0-0 \
    libsdl2-dev

print_success "SDL2 libraries installed"

# 2. Fix permissions
print_header "Fixing Permissions"

# Add user to required groups
for group in video render input; do
    if ! groups $USER | grep -q $group; then
        print_info "Adding $USER to $group group"
        sudo usermod -a -G $group $USER
        print_success "Added to $group group"
    else
        print_info "$USER already in $group group"
    fi
done

# Set framebuffer permissions
if [ -e /dev/fb0 ]; then
    print_info "Setting framebuffer permissions"
    sudo chmod g+rw /dev/fb0
    print_success "Framebuffer permissions updated"
fi

# 3. Configure boot settings for DSI
print_header "Configuring Boot Settings"

CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    CONFIG_FILE="/boot/config.txt"
fi

print_info "Backing up $CONFIG_FILE"
sudo cp $CONFIG_FILE ${CONFIG_FILE}.backup.$(date +%Y%m%d-%H%M%S)

# Check current settings
if ! grep -q "^dtoverlay=vc4-kms-v3d" $CONFIG_FILE; then
    print_info "Adding KMS overlay for DSI display"
    sudo bash -c "cat >> $CONFIG_FILE << EOF

# RPIFrame DSI Display Settings
dtoverlay=vc4-kms-v3d
display_auto_detect=1
disable_overscan=1
hdmi_force_hotplug=0
EOF"
    REBOOT_REQUIRED=true
else
    print_info "KMS overlay already configured"
fi

# 4. Create udev rules for persistent permissions
print_header "Creating udev Rules"

print_info "Creating framebuffer udev rules"
sudo bash -c 'cat > /etc/udev/rules.d/99-framebuffer.rules << EOF
# Framebuffer permissions for RPIFrame
SUBSYSTEM=="graphics", KERNEL=="fb*", MODE="0666", GROUP="video"
SUBSYSTEM=="drm", MODE="0666", GROUP="video"
EOF'

sudo udevadm control --reload-rules
sudo udevadm trigger
print_success "udev rules created"

# 5. Test SDL2 availability
print_header "Testing SDL2"

# Create a simple SDL test
cat > /tmp/test_sdl.c << 'EOF'
#include <SDL2/SDL.h>
#include <stdio.h>

int main(int argc, char* argv[]) {
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL could not initialize! Error: %s\n", SDL_GetError());
        return 1;
    }
    
    int num_drivers = SDL_GetNumVideoDrivers();
    printf("Available SDL video drivers:\n");
    for (int i = 0; i < num_drivers; i++) {
        printf("  - %s\n", SDL_GetVideoDriver(i));
    }
    
    SDL_Quit();
    return 0;
}
EOF

# Compile and run test
if gcc -o /tmp/test_sdl /tmp/test_sdl.c `sdl2-config --cflags --libs` 2>/dev/null; then
    print_info "SDL2 test compiled successfully"
    /tmp/test_sdl
else
    print_error "SDL2 test compilation failed"
fi

# 6. Set up environment
print_header "Setting Up Environment"

# Create environment setup script
cat > ~/RPIFrame/setup_display_env.sh << 'EOF'
#!/bin/bash
# Environment setup for RPIFrame display

# Try KMS driver first
export SDL_VIDEODRIVER=kmsdrm

# Fallback options
# export SDL_VIDEODRIVER=fbdev
# export SDL_FBDEV=/dev/fb0

# Ensure Python finds the modules
export PYTHONPATH=/home/$USER/RPIFrame:$PYTHONPATH

echo "Display environment configured:"
echo "  SDL_VIDEODRIVER=$SDL_VIDEODRIVER"
echo "  Groups: $(groups)"
echo "  Framebuffer: $(ls /dev/fb* 2>/dev/null || echo 'none found')"
echo "  DRM devices: $(ls /dev/dri/ 2>/dev/null || echo 'none found')"
EOF

chmod +x ~/RPIFrame/setup_display_env.sh
print_success "Environment setup script created"

# 7. Summary
print_header "Summary"

echo "Actions performed:"
echo "  • Installed SDL2 libraries"
echo "  • Added user to video, render, input groups"
echo "  • Configured boot settings for DSI display"
echo "  • Created udev rules for device permissions"
echo "  • Created environment setup script"
echo

if [ "$REBOOT_REQUIRED" = true ]; then
    echo -e "${YELLOW}IMPORTANT: Reboot required for changes to take effect${NC}"
    echo
fi

echo "Next steps:"
echo "1. Log out and back in (or reboot) for group changes"
echo "2. Run: source ~/RPIFrame/setup_display_env.sh"
echo "3. Test with: python ~/RPIFrame/diagnose_display.py"
echo "4. If working, restart service: sudo systemctl restart rpiframe.service"

print_success "Display fix script completed!"