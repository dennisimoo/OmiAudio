# Omi Audio Transcriber

A simple web application that allows you to record audio and transcribe it using OpenAI's Whisper model from Omi devices.


## Features

- Record audio from client devices
- Store audio files on the server
- Transcribe audio files using OpenAI's Whisper model
- View and select from all previously recorded audio files
- On-demand transcription of any stored audio file
- Responsive UI for both desktop and mobile

## Requirements

- Python 3.6+
- FFmpeg (for audio processing)
- OpenAI API key

## Installation

### Local Installation

1. Clone this repository
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Install FFmpeg if you don't have it already:
   - **Mac (using Homebrew)**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `apt-get install ffmpeg`
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)

4. Create a `.env` file in the project root and add your OpenAI API key:

```
OPENAI_API_KEY="your_api_key_here"
```

### Docker Installation

1. Clone this repository
2. Create a `.env` file as described above
3. Build and run the Docker container:

```bash
docker build -t omi-audio-transcriber .
docker run -p 5000:5000 -v $(pwd)/saved_audio:/app/saved_audio -v $(pwd)/transcripts:/app/transcripts --env-file .env omi-audio-transcriber
```

## Usage

### Running Locally

1. Start the server:

```bash
python run_server.py
```

2. The server will run at http://localhost:5001

### Using the Service

1. To record audio:
   - POST audio data to the root endpoint ("/") with parameters `uid` and `sample_rate`
   - Example: `curl -X POST --data-binary @audio.wav "http://localhost:5001/?uid=user123&sample_rate=44100"`

2. To transcribe existing audio files:
   - Navigate to http://localhost:5001/transcribe in your browser (or port 5000 if using Docker)
   - Select an audio file from the list
   - Click the "Transcribe" button
   - View the transcribed text in the right panel

### Accessing from Other Devices

To make the service accessible from other devices, you can use ngrok.

1.  Install ngrok: `brew install ngrok` (or download from [ngrok website](https://ngrok.com/download))
2.  Run ngrok to expose the local port: `ngrok http 5001`
   * You may need to sign up for a free ngrok account to use this command.
3.  Use the provided ngrok URL (e.g., `https://your-ngrok-url.ngrok.io`) to access the service from other devices.

See [ACCESS.md](ACCESS.md) for instructions on accessing the service from other devices on your network and installing FFmpeg. This file provides guidance on installing FFmpeg for audio processing and accessing the Omi Audio Transcriber from other devices on your local network.

## API Endpoints

- `GET /`: Health check
- `POST /`: Upload audio
- `GET /transcript/<filename>`: Get a specific transcript
- `GET /transcribe`: Web interface for selecting and transcribing audio files
- `GET /list_audio_files`: API to get a list of all available audio files
- `GET /transcribe_audio/<filename>`: API to transcribe a specific audio file

## Directories

- `saved_audio/`: Stores all uploaded audio files
- `transcripts/`: Stores all transcription results

## Troubleshooting

- If audio processing doesn't work, make sure FFmpeg is installed and available in your PATH
- If transcription fails, check that your OpenAI API key is valid and set correctly in the .env file
