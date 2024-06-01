import sys
import whisper

def transcribe(audio_path):
    model = whisper.load_model("base")  # You can choose different model sizes
    result = model.transcribe(audio_path)
    print(result['text'])  # Use print to send data back to Node.js

if __name__ == "__main__":
    transcribe(sys.argv[1])
