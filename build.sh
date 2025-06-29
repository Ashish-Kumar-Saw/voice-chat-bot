#!/bin/bash
set -e  # Exit on error

echo "==> Installing system dependencies..."
apt-get update -y
apt-get install -y portaudio19-dev libsdl2-dev libsdl2-mixer-2.0-0 python3-dev

echo "==> Installing Python dependencies in specific order..."
pip install --upgrade pip
pip install wheel setuptools

# Install problematic packages
pip install PyAudio==0.2.14
pip install pygame==2.5.2

# Install remaining packages
pip install -r requirements.txt

# Check Python version and modules
python --version
python -c "import sys; print(sys.path)"