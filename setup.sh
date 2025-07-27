#!/bin/bash

# This script sets up the KROMV12 project

echo "Setting up KROMV12 project..."

# Go to the KROMV12 directory
cd /Users/marcschwyn/Desktop/projects/KROMV12

# Install npm dependencies
echo "Installing dependencies..."
npm install

# Create data directory
mkdir -p data

echo "Setup complete! You can now run:"
echo "  cd /Users/marcschwyn/Desktop/projects/KROMV12"
echo "  node krom-poller-local.js"