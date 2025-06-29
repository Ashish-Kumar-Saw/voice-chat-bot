#!/bin/bash
set -e  # Exit on error

echo "==> Installing system dependencies..."
apt-get update -y
apt-get install -y portaudio19-dev libsdl2-dev libsdl2-mixer-2.0-0

echo "==> Verifying SDL2 installation..."
ls -la /usr/include/SDL2
which sdl2-config || echo "sdl2-config not found"

echo "==> Installing Python dependencies in specific order..."
pip install --upgrade pip
pip install wheel setuptools

# Install problematic packages using pre-built binaries
pip install PyAudio==0.2.14
pip install --no-build-isolation pygame==2.5.2

# Install remaining packages
pip install -r requirements.txt