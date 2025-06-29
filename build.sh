#!/usr/bin/env bash
# build.sh - Custom build script for Render deployment

# Install system dependencies first
apt-get update -y
apt-get install -y portaudio19-dev libsdl2-dev libsdl2-mixer-2.0-0

# Now install Python dependencies
pip install -r requirements.txt