# Accessing the Omi Audio Transcriber from Other Devices

## Install FFmpeg

To fix the FFmpeg warning and enable proper audio processing:

### On macOS:
```bash
brew install ffmpeg
```

### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### On Windows:
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract the files to a folder like `C:\ffmpeg`
3. Add the bin folder to your PATH environment variable

After installing FFmpeg, restart the server to apply the changes.

## Accessing from Other Devices on Your Network

The server is already configured to run on all network interfaces (`0.0.0.0`) which makes it accessible from other devices on your local network. Here's how to access it:

1. Find your computer's IP address:
   - On macOS/Linux: Open Terminal and type `ifconfig` or `ip addr show`
   - On Windows: Open Command Prompt and type `ipconfig`
   
   Look for your WiFi or Ethernet connection and note the IP address (something like `192.168.1.x` or `10.0.0.x`)

2. On other devices on the same network, open a web browser and navigate to:
   ```
   http://YOUR_IP_ADDRESS:5003/transcribe
   ```
   Replace `YOUR_IP_ADDRESS` with the IP address you found in step 1.

3. If the connection is refused, check that:
   - The server is running
   - Your firewall isn't blocking port 5003
   - Both devices are on the same network

### Example:
If your IP address is `192.168.1.100`, you would access the application from another device using:
```
http://192.168.1.100:5003/transcribe
```

## Troubleshooting Network Access

- **Firewall Issues**: You might need to allow incoming connections on port 5003.
- **Router Restrictions**: Some networks restrict device-to-device communications.
- **Port in Use**: If port 5003 is already in use, edit `run_server.py` to use a different port.
