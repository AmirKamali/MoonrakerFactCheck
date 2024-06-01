#POC: Continous Basic Whisper script that grabs 5 seconds of audio and converts to text
#MPC/5.29.24

import warnings

# Suppress tie specific warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

print("============[ WHISPER CAPTURE ]==============")

import sounddevice as sd
import numpy as np
import whisper

samplerate = 16000  # 16kHz
duration = 5  # seconds
model = whisper.load_model("medium")

def record_audio():
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()
    return audio

def transcribe_audio(audio_data):
    audio_np = np.squeeze(audio_data)
    audio_float = audio_np.astype(np.float32) / np.iinfo(np.int16).max
    result = model.transcribe(audio_float)
    return result['text']

def does_not_contains_and_cut(input_string):
    # Convert the input string to lower case
    lower_case_string = input_string.lower()
    
    # Check if "and cut" is in the lower-case version of the string
    if "and cut" in lower_case_string:
        return False
    else:
        return True

transcription = "fuck"
while (does_not_contains_and_cut(transcription)):
    audio_data = record_audio()
    transcription = transcribe_audio(audio_data)
    print("Transcription:", transcription)
