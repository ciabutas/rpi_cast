#!/bin/sh

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.6" | bc -l) )); then
    echo "Python 3.6 or higher is required. Current version: $python_version"
    exit 1
fi

# Install required system packages
apt-get update
apt-get install -y python3-full python3-venv git wget vlc libnss-mdns fbi python3-dev

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

# Enable and start the service
systemctl enable raspberrycast
systemctl start raspberrycast

echo "Installation complete!"
