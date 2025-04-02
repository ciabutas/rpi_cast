#!/bin/sh

# Check Python version
python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.6" | bc -l) )); then
    echo "Python 3.6 or higher is required. Current version: $python_version"
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for required commands
for cmd in pip git wget omxplayer; do
    if ! command -v $cmd >/dev/null 2>&1; then
        echo "Required command not found: $cmd"
        echo "Installing required packages..."
        apt-get update
        apt-get install -y python3-pip git wget omxplayer libnss-mdns fbi
        break
    fi
done

# Backup existing configuration
if [ -f "/home/$USER/RaspberryCast/raspberrycast.conf" ]; then
    echo "Backing up existing configuration..."
    cp "/home/$USER/RaspberryCast/raspberrycast.conf" "/home/$USER/raspberrycast.conf.backup"
fi

if [ `id -u` -ne 0 ]
then
  echo "Please run this script with root privileges!"
  echo "Try again with sudo."
  exit 0
fi

echo "This script will install RaspberryCast"

read -p "Which user do you want to install RaspberryCast as? (Leave blank to set to default): " USER

if ! [ -n "$USER" ]; then
    echo "Setting user to default value 'pi'."
    USER="pi"
fi

if ! getent passwd $USER > /dev/null 2>&1; then
    echo "User $USER does not exist. Exiting."
    exit
fi

echo "Your system will be rebooted on completion"
echo "Do you wish to continue? (y/n)"

while true; do
  read -p "" yn
  case $yn in
      [Yy]* ) break;;
      [Nn]* ) exit 0;;
      * ) echo "Please answer with Yes or No [y|n].";;
  esac
done
echo ""
echo "============================================================"
echo ""
echo "Installing necessary dependencies... (This could take a while)"
echo ""
echo "============================================================"

apt-get install -y lsof python-pip git wget omxplayer libnss-mdns fbi
echo "============================================================"

if [ "$?" = "1" ]
then
  echo "An unexpected error occured during apt-get!"
  exit 0
fi

pip install yt-dlp bottle livestreamer

if [ "$?" = "1" ]
then
  echo "An unexpected error occured during pip install!"
  exit 0
fi

echo ""
echo "============================================================"
echo ""
echo "Cloning project from GitHub.."
echo ""
echo "============================================================"

su - $USER -c "git clone https://github.com/ciabutas/RaspberryCast.git"
chmod +x ./RaspberryCast/RaspberryCast.sh

echo ""
echo "============================================================"
echo ""
echo "Adding project to startup sequence and custom options"
echo ""
echo "============================================================"

#Gives right to all user to get out of screen standby
chmod 666 /dev/tty1

#Add to rc.local startup
sed -i '$ d' /etc/rc.local
echo "su - $USER -c \"cd ./RaspberryCast/ && ./RaspberryCast.sh start\"" >> /etc/rc.local
echo "exit 0" >> /etc/rc.local

#Adding right to current pi user to shutdown
chmod +s /sbin/shutdown

#Adding right to sudo fbi without password
echo "$USER ALL = (root) NOPASSWD: /usr/bin/fbi" >> /etc/sudoers

rm setup.sh

echo "============================================================"
echo "Setup was successful."
echo "Do not delete the 'RaspberryCast' folder as it contains all application data!"
echo "Rebooting system now..."
echo "============================================================"

sleep 2

#Reboot to ensure cleaness of Pi memory and displaying of log
reboot

exit 0
