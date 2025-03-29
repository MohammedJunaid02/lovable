import os
import uuid
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from moviepy import VideoFileClip
from pydantic import BaseModel

app = FastAPI(
    title="Video to Audio Conversion API",
    description="API service to extract audio from video files",
    version="1.0.0"
)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

class ErrorResponse(BaseModel):
    error: str

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_audio_moviepy(video_path: str, audio_path: str) -> tuple[bool, str]:
    """
    Extracts audio from a video file using MoviePy.

    Args:
        video_path (str): Path to the input video file.
        audio_path (str): Path where the output audio file will be saved.
                          The extension determines the format.
    
    Returns:
        tuple: (success_flag, message)
    """
    try:
        # Check if video file exists
        if not os.path.exists(video_path):
            return False, f"Error: Video file not found at '{video_path}'"

        # Load the video file
        with VideoFileClip(video_path) as video_clip:
            # Check if the video clip has an audio track
            if video_clip.audio is None:
                return False, f"Error: No audio track found in '{video_path}'"

            # Extract the audio
            audio_clip = video_clip.audio

            # Write the audio file
            audio_clip.write_audiofile(audio_path, verbose=False, logger=None)

        return True, "Audio extraction successful!"

    except Exception as e:
        return False, f"An error occurred during audio extraction: {str(e)}"

@app.post("/convert", 
    responses={
        200: {"content": {"audio/mpeg": {}, "audio/wav": {}, "audio/ogg": {}, "audio/aac": {}}},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Convert video to audio",
    description="Upload a video file and convert it to audio in the specified format"
)
async def convert_video_to_audio(
    file: UploadFile = File(..., description="The video file to convert"),
    format: str = Form("mp3", description="Output audio format (mp3, wav, ogg, aac)")
):
    # Check if the format is supported
    if format.lower() not in ['mp3', 'wav', 'ogg', 'aac']:
        raise HTTPException(status_code=400, detail=f"Unsupported output format: {format}")
    
    # Check if the file format is allowed
    if not file.filename or not allowed_file(file.filename):
        allowed_formats = ', '.join(ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file format. Allowed formats: {allowed_formats}"
        )
    
    # Generate unique filenames
    unique_id = str(uuid.uuid4())
    filename = file.filename.replace(" ", "_")  # Simple filename sanitization
    base_filename = os.path.splitext(filename)[0]
    
    video_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
    audio_path = os.path.join(OUTPUT_FOLDER, f"{unique_id}_{base_filename}.{format}")
    
    # Save uploaded file
    try:
        content = await file.read()
        with open(video_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")
    
    # Extract audio
    success, message = extract_audio_moviepy(video_path, audio_path)
    
    # Clean up video file after processing
    if os.path.exists(video_path):
        os.remove(video_path)
    
    if success:
        # Return audio file for download
        return FileResponse(
            path=audio_path,
            filename=f"{base_filename}.{format}",
            media_type=f"audio/{format}"
        )
    else:
        raise HTTPException(status_code=500, detail=message)

@app.get("/health", 
    response_model=dict,
    summary="Health check endpoint",
    description="Returns the health status of the API"
)

@app.get("/", summary="Welcome endpoint", description="Displays a welcome message for the API")
async def welcome():
    return {"message": "Welcome to the Video to Audio Conversion API! Use /convert to extract audio from videos."}


async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)