#!/bin/bash

echo "Installing dependencies..."
# Update and install system packages (fixes compilation errors)
pkg update -y
pkg install python git rust clang python-cryptography python-psutil python-pillow -y

# Remove old folder if it exists to ensure clean install
rm -rf tg-ws-proxy-android

echo "Cloning repository..."
git clone https://github.com/Superdetectiv4ik/tg-ws-proxy-android.git
cd tg-ws-proxy-android

echo "Creating config file..."
# Create config directory and file
mkdir -p ~/TgWsProxy
cat << 'EOF' > ~/TgWsProxy/config.json
{
  "port": 1080,
  "host": "127.0.0.1",
  "dc_ip": ["5:91.108.56.190"],
  "verbose": false
}
EOF

echo "Installing Python requirements..."
pip install -r requirements.txt

echo "Setup complete!"
echo "Acquiring Wake Lock (keeps Android from sleeping)..."
termux-wake-lock

echo "Starting Proxy..."
python main.py
