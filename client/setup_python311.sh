#!/bin/bash

# Setup script to use Python 3.11 for the custom-streamlit-mcp project

echo "Setting up Python 3.11 environment for custom-streamlit-mcp..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found. Installing via Homebrew..."
    brew install python@3.11
fi

# Install dependencies with Python 3.11
echo "Installing dependencies with Python 3.11..."
pip3.11 install -r requirements.txt

echo "Setup complete! You can now run the Streamlit app with:"
echo "python3.11 -m streamlit run app.py"
echo ""
echo "Or update your IDE to use Python 3.11 interpreter:"
echo "Python executable: $(which python3.11)"
