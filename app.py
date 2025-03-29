from flask import Flask, request, jsonify
import os
import shutil
from moviepy import VideoFileClip
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Directories for storing files
UPLOAD_DIR = "uploads"
AUDIO_DIR = "audio_outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

def extract_audio(video_path, audio_path):
    """ Extracts audio from a video file and saves it. """
    try:
        with VideoFileClip(video_path) as video_clip:
            if video_clip.audio is None:
                return False
            video_clip.audio.write_audiofile(audio_path)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

@app.route('/extract-audio', methods=['POST'])
def extract_audio_api():
    """ API to upload a video file and extract its audio. """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    output_format = request.form.get('output_format', 'mp3')  # Default format is MP3

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    video_path = os.path.join(UPLOAD_DIR, filename)
    audio_filename = f"{os.path.splitext(filename)[0]}.{output_format}"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)

    # Save uploaded video file
    file.save(video_path)

    # Extract audio
    if extract_audio(video_path, audio_path):
        return jsonify({"message": "Audio extracted successfully", "audio_file": audio_path})
    else:
        return jsonify({"error": "Failed to extract audio"}), 500

if __name__ == '__main__':
    app.run(debug=True)
