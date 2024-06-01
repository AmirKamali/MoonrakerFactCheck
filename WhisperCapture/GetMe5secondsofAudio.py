#POC: Basic Whisper script that grabs 5 seconds of audio and converts to text
#MPC/5.29.24

import warnings

# Suppress the specific warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

print("============[ WHISPER CAPTURE ]==============")

# Capture Audio Input
import sounddevice as sd
import numpy as np
import whisper

# Settings
samplerate = 16000  # 16kHz
duration = 5  # seconds

# Simple recording
def record_audio():
    print("And, Recording... START TALKING FOR 5 SECONDS!")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    print("OK, And that's a wrap, Ship It")
    return audio

audio_data = record_audio()

# Process Audio with Whisper
# Load the Whisper model
model = whisper.load_model("medium")

def transcribe_audio(audio_data):
    # Convert audio to a format Whisper can process
    audio_np = np.squeeze(audio_data)
    audio_float = audio_np.astype(np.float32) / np.iinfo(np.int16).max

    # Transcribe audio using Whisper
    result = model.transcribe(audio_float)
    return result['text']

transcription = transcribe_audio(audio_data)
print("Here's what we heard:", transcription)
print("============[ DONE ]============")
