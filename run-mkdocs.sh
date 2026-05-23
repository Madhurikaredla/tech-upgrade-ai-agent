#!/bin/bash

# Check if Python3 exists
if ! command -v python3 &> /dev/null
then
    echo "Python3 not found. Please install Python first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip once (optional)
# pip install --upgrade pip

# Install packages from mkdocs_deps.txt
if [ -f "mkdocs_deps.txt" ]; then
    echo "Installing missing packages from mkdocs_deps.txt..."
    pip install --upgrade -r mkdocs_deps.txt
else
    echo "mkdocs_deps.txt not found!"
fi

# Run MkDocs server
echo "Starting MkDocs server..."
mkdocs serve
