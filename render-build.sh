#!/usr/bin/env bash
# Render build script: install backend + frontend deps, build frontend
set -o errexit

# Install Python dependencies
pip install -r backend/requirements.txt

# Install Node and build frontend
cd frontend
npm install
npm run build
cd ..
