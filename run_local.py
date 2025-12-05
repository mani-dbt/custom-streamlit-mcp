#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    """Run the Streamlit app locally."""
    # Ensure we're in the client directory
    os.chdir('client')
    
    # Run streamlit
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])

if __name__ == "__main__":
    main()