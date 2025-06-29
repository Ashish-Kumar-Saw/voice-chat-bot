#!/usr/bin/env bash
# Install system dependencies
apt-get update -y
apt-get install -y portaudio19-dev libsdl2-dev libsdl2-mixer-2.0-0

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt