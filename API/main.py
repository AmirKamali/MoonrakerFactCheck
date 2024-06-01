from typing import Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import whisper

ABSOLUTE_PATH = "/Users/saig/Documents/Code/Hackathons/MoonrakerFactCheck/"

app = FastAPI()
model = whisper.load_model("base")

# Define a Pydantic model for the request body
class AudioSubmission(BaseModel):
    chunk_id: int
    

@app.get("/")
def read_root():
    return {"Hello": "FactWhisper"}


@app.post("/fact_check/")
async def fact_check(request: AudioSubmission) -> dict:
    try:
        # Extract audio file
        audio_file_path = await audio_path(request.chunk_id)
        
        # Generate transcript using Whisper
        transcript = await fetch_whisper(audio_file_path)
        
        return {"transcript": transcript}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    

async def audio_path(chunk_id) -> str:
    # Construct the expected filename
    expected_filename = f"{chunk_id}.mp3"
    directory = os.path.join(ABSOLUTE_PATH, "API/Audio_Files/")
    
    audio_file_path = None
    # Asynchronously check the directory for the file
    for root, _, files in os.walk(directory):
        if expected_filename in files:
            audio_file_path = os.path.join(root, expected_filename)
    
    if audio_file_path == None:
        # If the file is not found, raise an exception
        raise FileNotFoundError(f"File with chunk_id {chunk_id} not found in directory {directory}")
    else:
        return audio_file_path
    
        
async def fetch_whisper(audio_file_path: str) -> str:
    result = model.transcribe(audio_file_path, fp16=False)
    
    return result["text"]
    
    