#!/bin/bash
set -e
# Install cmake (required for dlib-bin)
pip install cmake

# Install precompiled dlib binary to prevent 8GB OOM during compilation
pip install dlib-bin

# Install face_recognition dependencies manually
pip install face_recognition_models Click Pillow

# Install face_recognition WITHOUT dependencies (so it doesn't trigger dlib source build)
pip install face-recognition --no-deps

# Install the rest of the project requirements
pip install -r requirements.txt
