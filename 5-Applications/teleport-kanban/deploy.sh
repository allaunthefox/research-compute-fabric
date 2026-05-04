#!/bin/bash

# Soliton Governor Deployment Script
# Deploys the BF16 Teleport Compression & Unified Substrate System with Thermodynamic State Machine

set -e

echo "🚀 Deploying BF16 Teleport Compression & Unified Substrate System"
echo "📍 Thermodynamic State Machine with Fail-Soft/Fail-Safe Modes"
echo

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root for MSR access and systemd installation"
   echo "Usage: sudo ./deploy.sh"
   exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Install prerequisites
echo "📦 Installing prerequisites..."
apt-get update
apt-get install -y msr-tools msr-dumper hwmon-tools lm-sensors

# Create msr group if it doesn't exist
if ! getent group msr > /dev/null 2>&1; then
    groupadd msr
    print_status "Created msr group"
else
    print_status "msr group already exists"
fi

# 2. Build the project
echo "🔨 Building the project..."
cd /home/allaun/Documents/teleport-kanban
cargo build --release

if [ $? -eq 0 ]; then
    print_status "Build successful"
else
    print_error "Build failed"
    exit 1
fi

# 3. Install the binary
echo "📋 Installing binary..."
cp target/release/teleport-kanban /usr/local/bin/
chmod +x /usr/local/bin/teleport-kanban
print_status "Binary installed to /usr/local/bin/teleport-kanban"

# 4. Install systemd service
echo "⚙️ Installing systemd service..."
cp soliton-governor.service /etc/systemd/system/
systemctl daemon-reload
print_status "Systemd service installed"

# 5. Install Udev rules
echo "🔧 Installing Udev rules..."
cp 99-msr.rules /etc/udev/rules.d/
udevadm control --reload-rules
udevadm trigger
print_status "Udev rules installed and activated"

# 6. Create msr user group and add current user
echo "👥 Setting up MSR access permissions..."
usermod -a -G msr $SUDO_USER
print_status "Added $SUDO_USER to msr group"

# 7. Create configuration directory
echo "📁 Creating configuration directory..."
mkdir -p /etc/teleport-kanban
mkdir -p /var/log/teleport-kanban
chown root:msr /etc/teleport-kanban
chmod 755 /etc/teleport-kanban
chown root:msr /var/log/teleport-kanban
chmod 755 /var/log/teleport-kanban
print_status "Configuration directories created"

# 8. Create logrotate configuration
echo "📝 Creating logrotate configuration..."
cat > /etc/logrotate.d/teleport-kanban << EOF
/var/log/teleport-kanban/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root msr
    postrotate
        systemctl reload soliton-governor || true
    endscript
}
EOF
print_status "Logrotate configuration created"

# 9. Test MSR access
echo "🧪 Testing MSR access..."
if [ -r /dev/cpu/0/msr ]; then
    print_status "MSR access verified"
else
    print_warning "MSR access may not be working. You may need to reboot."
fi

# 10. Enable and start the service
echo "🚀 Enabling and starting service..."
systemctl enable soliton-governor
systemctl start soliton-governor

if systemctl is-active --quiet soliton-governor; then
    print_status "Service started successfully"
else
    print_error "Service failed to start"
    systemctl status soliton-governor
    exit 1
fi

# 11. Display status
echo
echo "📊 System Status:"
echo "   Service Status: $(systemctl is-active soliton-governor)"
echo "   Service Enabled: $(systemctl is-enabled soliton-governor)"
echo "   MSR Access: $(ls -la /dev/cpu/0/msr 2>/dev/null | awk '{print $1}')"
echo "   Log Directory: /var/log/teleport-kanban/"
echo

# 12. Show monitoring commands
echo "🔍 Monitoring Commands:"
echo "   View service status: systemctl status soliton-governor"
echo "   View logs: journalctl -u soliton-governor -f"
echo "   View thermodynamic metrics: tail -f /var/log/teleport-kanban/*.log"
echo "   Check MSR access: sudo rdmsr 0xC00102E3"
echo

# 13. Post-installation notes
echo "📝 Post-Installation Notes:"
echo "   • You may need to reboot for full MSR access"
echo "   • The thermodynamic governor runs on CPU 0 (Core 0)"
echo "   • System will automatically transition between Ground/Metastable/ThermalMax states"
echo "   • Emergency fallback triggers at 95°C"
echo "   • P-State control adjusts CPU frequency and voltage based on thermal state"
echo

print_status "🎉 Deployment Complete!"
print_status "Your BF16 Teleport Compression & Unified Substrate System is now running"
print_status "with thermodynamic state machine and fail-soft/fail-safe modes!"

echo
echo "💡 Quick Start:"
echo "   • Monitor system: journalctl -u soliton-governor -f"
echo "   • Check thermodynamic state: systemctl status soliton-governor"
echo "   • View compression stats: tail -f /var/log/teleport-kanban/*.log"
echo "   • Emergency stop: systemctl stop soliton-governor"