#!/usr/bin/env python3
"""
Run script for Omi Audio Transcriber server
"""
import os
import sys
import subprocess

print("Starting Omi Audio Transcriber server...")

# Check Python version
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
print(f"Python version: {python_version}")

# Check dependencies
try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError:
    print("ERROR: Flask is not installed. Please install it with: pip install flask")
    sys.exit(1)

try:
    from pydub import AudioSegment
    print("pydub is installed")
except ImportError:
    print("ERROR: pydub is not installed. Please install it with: pip install pydub")
    sys.exit(1)

try:
    from openai import OpenAI
    print("OpenAI SDK is installed")
except ImportError:
    print("ERROR: OpenAI SDK is not installed. Please install it with: pip install openai")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print("python-dotenv is installed")
except ImportError:
    print("ERROR: python-dotenv is not installed. Please install it with: pip install python-dotenv")
    sys.exit(1)

# Check ffmpeg
try:
    subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    print("ffmpeg is installed")
except (FileNotFoundError, subprocess.SubprocessError):
    print("WARNING: ffmpeg is not installed or not found in PATH. Audio processing may not work correctly.")
    print("Install ffmpeg (https://ffmpeg.org/) and ensure it's in your PATH.")

# Load environment variables
load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    print("WARNING: OPENAI_API_KEY is not set in .env file")
else:
    print("OPENAI_API_KEY is set")

# Import and run the app
try:
    import app
    print("App module imported successfully")
    print("\nStarting the server on port 5003...")
    app.app.run(host='0.0.0.0', port=5003, debug=True)
except Exception as e:
    print(f"ERROR: Failed to start the server: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
