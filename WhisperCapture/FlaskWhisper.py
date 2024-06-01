from flask import Flask, request, jsonify
import sounddevice as sd
import numpy as np
import whisper

app = Flask(__name__)
samplerate = 16000  # 16kHz
duration = 5  # seconds
model = whisper.load_model("base")

def record_audio():
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()
    return audio

def transcribe_audio(audio_data):
    audio_np = np.squeeze(audio_data)
    audio_float = audio_np.astype(np.float32) / np.iinfo(np.int16).max
    result = model.transcribe(audio_float)
    return result['text']

@app.route('/listen', methods=['GET'])
def listen():
    audio_data = record_audio()
    transcription = transcribe_audio(audio_data)
    return jsonify({'transcription': transcription})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)


