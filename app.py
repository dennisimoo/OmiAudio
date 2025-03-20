import os
import io
import logging
from flask import Flask, request, jsonify, send_file, render_template_string, url_for
from datetime import datetime
from pydub import AudioSegment
import openai
import glob
import re
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define directories
LOCAL_AUDIO_DIR = "saved_audio"
TRANSCRIPT_DIR = "transcripts"
os.makedirs(LOCAL_AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

# Initialize OpenAI client
from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# HTML Template for the transcription page
TRANSCRIBE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Omi Audio Transcriber</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1, h2 {
            color: #333;
        }
        .container {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .panel {
            flex: 1;
            min-width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            background-color: #f9f9f9;
        }
        .file-list {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background-color: white;
        }
        .audio-item {
            margin-bottom: 8px;
            padding: 8px;
            cursor: pointer;
            border-radius: 4px;
        }
        .audio-item:hover {
            background-color: #f0f0f0;
        }
        .audio-item.selected {
            background-color: #e0e7ff;
        }
        .timestamp {
            color: #888;
            font-size: 0.8em;
            display: block;
        }
        .button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 10px 0;
            cursor: pointer;
            border-radius: 4px;
        }
        .button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        audio {
            width: 100%;
            margin: 10px 0;
        }
        .transcript-text {
            white-space: pre-wrap;
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            background-color: white;
        }
        .status {
            margin-top: 10px;
            font-style: italic;
        }
        .error {
            color: red;
        }
        .success {
            color: green;
        }
    </style>
</head>
<body>
    <h1>Omi Audio Transcriber</h1>
    
    <div class="container">
        <div class="panel">
            <h2>Available Audio Files</h2>
            <div id="file-list" class="file-list">Loading audio files...</div>
            <button id="transcribe-button" class="button" disabled>Transcribe Selected Audio</button>
            <div id="status" class="status"></div>
        </div>
        
        <div class="panel">
            <h2>Audio Player</h2>
            <div id="player-container">
                <div id="no-audio-message">Select an audio file to play</div>
                <audio id="audio-player" controls style="display: none;"></audio>
            </div>
            <h2>Transcription Result</h2>
            <div id="transcript-result" class="transcript-text">Select an audio file and click "Transcribe" to get started.</div>
        </div>
    </div>
    
    <script>
        // State
        let selectedAudioFile = null;
        
        // DOM Elements
        const audioPlayer = document.getElementById('audio-player');
        const fileList = document.getElementById('file-list');
        const transcriptResult = document.getElementById('transcript-result');
        const transcribeButton = document.getElementById('transcribe-button');
        const statusElement = document.getElementById('status');
        
        // Fetch audio files
        async function fetchAudioFiles() {
            try {
                const response = await fetch('/list_audio_files');
                const data = await response.json();
                
                if (data.status === 'success') {
                    if (data.audio_files.length === 0) {
                        fileList.innerHTML = '<p>No audio files available.</p>';
                        return;
                    }
                    
                    // Sort audio files by date (newest first)
                    data.audio_files.sort((a, b) => {
                        return new Date(b.timestamp) - new Date(a.timestamp);
                    });
                    
                    let html = '';
                    for (const file of data.audio_files) {
                        const shortName = file.filename.split('_')[1] || file.filename;
                        const timestamp = new Date(file.timestamp).toLocaleString();
                        
                        html += `<div class="audio-item" data-file="${file.filename}" onclick="selectAudioFile(this, '${file.filename}')">
                            ${shortName}
                            <span class="timestamp">${timestamp}</span>
                        </div>`;
                    }
                    
                    fileList.innerHTML = html;
                } else {
                    fileList.innerHTML = `<p class="error">Error loading audio files: ${data.message}</p>`;
                }
            } catch (error) {
                fileList.innerHTML = `<p class="error">Error loading audio files: ${error.message}</p>`;
            }
        }
        
        // Select an audio file
        function selectAudioFile(element, filename) {
            // Update selection state
            const selected = document.querySelector('.audio-item.selected');
            if (selected) {
                selected.classList.remove('selected');
            }
            element.classList.add('selected');
            selectedAudioFile = filename;
            
            // Enable the transcribe button
            transcribeButton.disabled = false;
            
            // Show the audio player
            document.getElementById('no-audio-message').style.display = 'none';
            audioPlayer.style.display = 'block';
            audioPlayer.src = `/audio_file/${filename}`;
            audioPlayer.load();
            
            // Reset transcript
            transcriptResult.innerText = 'Click "Transcribe" to process this audio file.';
            statusElement.innerText = '';
        }
        
        // Transcribe the selected audio file
        async function transcribeAudio() {
            if (!selectedAudioFile) return;
            
            // Update UI state
            transcribeButton.disabled = true;
            statusElement.innerText = 'Transcribing audio file...';
            transcriptResult.innerText = 'Processing...';
            
            try {
                const response = await fetch(`/transcribe_audio/${selectedAudioFile}`);
                const data = await response.json();
                
                if (data.status === 'success') {
                    statusElement.innerHTML = '<span class="success">Transcription completed successfully!</span>';
                    transcriptResult.innerText = data.transcript;
                } else {
                    statusElement.innerHTML = `<span class="error">Error: ${data.message}</span>`;
                    transcriptResult.innerText = 'Transcription failed. Please try again.';
                }
            } catch (error) {
                statusElement.innerHTML = `<span class="error">Error: ${error.message}</span>`;
                transcriptResult.innerText = 'Transcription failed. Please try again.';
            } finally {
                transcribeButton.disabled = false;
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            fetchAudioFiles();
            transcribeButton.addEventListener('click', transcribeAudio);
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return "Omi Audio Endpoint is running. Use POST to send audio data or go to /transcribe to view files.", 200

@app.route('/', methods=['POST'])
def receive_audio():
    try:
        uid = request.args.get("uid")
        sample_rate = int(request.args.get("sample_rate"))
        audio_bytes = request.data

        # Create audio segment from raw data
        audio_segment = AudioSegment(
            data=audio_bytes,
            sample_width=2,
            frame_rate=sample_rate,
            channels=1
        )

        # Save audio file
        filename = f"audio_{uid}_{datetime.utcnow().isoformat()}.wav"
        filepath = os.path.join(LOCAL_AUDIO_DIR, filename)
        audio_segment.export(filepath, format="wav")
        
        # Return success response
        return jsonify({
            "status": "success",
            "filename": filename,
            "message": "Audio received successfully. Go to /transcribe to view."
        }), 200

    except Exception as e:
        logger.error(f"Error in receive_audio: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/transcribe')
def transcribe_page():
    """Serve the audio transcription page"""
    return render_template_string(TRANSCRIBE_HTML)

@app.route('/audio_file/<filename>')
def get_audio_file(filename):
    """Serve an audio file for playback"""
    filepath = os.path.join(LOCAL_AUDIO_DIR, filename)
    return send_file(filepath, mimetype='audio/wav')

@app.route('/list_audio_files')
def list_audio_files():
    """Return a list of all available audio files"""
    try:
        audio_files = glob.glob(os.path.join(LOCAL_AUDIO_DIR, "*.wav"))
        files_data = []

        for file_path in audio_files:
            filename = os.path.basename(file_path)
            # Extract timestamp from filename
            match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)', filename)
            timestamp = match.group(1) if match else ''

            files_data.append({
                'filename': filename,
                'timestamp': timestamp,
                'path': file_path
            })

        return jsonify({"status": "success", "audio_files": files_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/transcribe_audio/<path:filename>', methods=['GET'])
def transcribe_audio(filename):
    """Transcribe a specific audio file using Whisper"""
    try:
        # Get the filepath
        filepath = os.path.join(LOCAL_AUDIO_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": f"Audio file not found: {filename}"}), 404
        
        # Check file size
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return jsonify({"status": "error", "message": "Audio file is empty"}), 400
        
        # Transcribe with GPT-4 mini and incorporate speaker identification
        # TODO: Implement GPT-4 mini transcription and speaker identification logic here
        logger.info(f"Transcribing file: {filepath}")
        with open(filepath, "rb") as audio_file:
            # Replace with GPT-4 mini transcription
            # Example: transcript_text = transcribe_with_gpt4_mini(audio_file)
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            transcript_text = response.text

            # Example of speaker identification (replace with actual implementation)
            # transcript_text = identify_speakers(transcript_text)
        
        # Save the transcript
        transcript_filename = f"transcript_{filename.replace('.wav', '')}.txt"
        transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_filename)
        with open(transcript_path, "w") as f:
            f.write(transcript_text)
            
        # Return success response
        return jsonify({
            "status": "success",
            "transcript": transcript_text,
            "filename": transcript_filename
        })

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/transcript/<filename>', methods=['GET'])
def get_transcript(filename):
    """Serve a transcript file"""
    filepath = os.path.join(TRANSCRIPT_DIR, filename)
    return send_file(filepath, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
