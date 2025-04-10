#!/bin/sh

# Store the script path
SCRIPT_PATH="$0"

# Function to cleanup and exit
cleanup() {
    local exit_code=$1
    echo "Cleaning up..."
    rm -f "$SCRIPT_PATH"
    exit "$exit_code"
}

# Error handler
handle_error() {
    echo "Error occurred during installation at line $1"
    cleanup 1
}

# Set error handler
trap 'handle_error $LINENO' ERR

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.6" | bc -l) )); then
    echo "Python 3.6 or higher is required. Current version: $python_version"
    cleanup 1
fi

# Install required system packages
apt-get update
apt-get install -y \
    python3-full \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    wget \
    vlc \
    libnss-mdns \
    fbi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv /opt/raspberrycast_venv

# Activate virtual environment and install Python packages
. /opt/raspberrycast_venv/bin/activate
pip install --no-cache-dir yt-dlp bottle livestreamer

# Update yt-dlp regularly (using absolute path to pip in venv)
echo "0 0 * * * /opt/raspberrycast_venv/bin/pip install -U yt-dlp" | crontab -

# Initial yt-dlp installation
/opt/raspberrycast_venv/bin/pip install -U yt-dlp

# Clone project if not already done
if [ ! -d "/home/$USER/RaspberryCast" ]; then
    su - $USER -c "git clone https://github.com/ciabutas/rpi_cast.git /home/$USER/RaspberryCast"
fi

# Update configuration to use VLC instead of omxplayer
cat > /home/$USER/RaspberryCast/raspberrycast.conf << EOF
{
    "slow_mode": true,
    "new_log": true,
    "pi_hostname": "raspberrypi",
    "width": "",
    "height": "",
    "subtitle_search": false,
    "player": "vlc"
}
EOF

# Create service file for systemd
cat > /etc/systemd/system/raspberrycast.service << EOF
[Unit]
Description=RaspberryCast Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/RaspberryCast
Environment=PATH=/opt/raspberrycast_venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/raspberrycast_venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set correct permissions
chown -R $USER:$USER /home/$USER/RaspberryCast
chmod -R 755 /home/$USER/RaspberryCast

# Enable and start the service
systemctl enable raspberrycast
systemctl start raspberrycast

echo "Installation complete!"

# Clean up the script
cleanup 0
