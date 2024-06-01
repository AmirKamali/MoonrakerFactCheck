let socket = io();
let recorder, gumStream, interval;
const recordButton = document.getElementById('recordButton');
const transcriptions = document.getElementById('transcriptions');

recordButton.addEventListener('click', () => {
    if (recorder && recorder.state === "recording") {
        // Stop recording
        recorder.stopRecording(() => {
            const blob = recorder.getBlob();
            sendData(blob);
            gumStream.getTracks().forEach(track => track.stop()); // Stop the media stream tracks
        });
        clearInterval(interval); // Clear the interval on stopping
        recorder = null;
        recordButton.textContent = "Record";
    } else {
        // Start recording
        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            gumStream = stream;
            recorder = RecordRTC(stream, {
                type: 'audio',
                mimeType: 'audio/webm', // Depending on browser support
                timeSlice: 10000, // On data available every 10 seconds
                ondataavailable: function(blob) {
                    sendData(blob);
                }
            });
            recorder.startRecording();
            recordButton.textContent = "Listening...";

            // Optionally, you can also set up the interval here if needed
            // interval = setInterval(() => {
            //     if (recorder) {
            //         recorder.stopRecording(() => {
            //             const blob = recorder.getBlob();
            //             sendData(blob);
            //             recorder.startRecording(); // Restart recording immediately
            //         });
            //     }
            // }, 10000);
        }).catch(err => {
            console.error('An error occurred: ' + err);
        });
    }
});

function sendData(blob) {
    let formData = new FormData();
    formData.append('audioData', blob, 'chunk.wav');
    fetch('/upload', { method: 'POST', body: formData })
    .then(response => response.text())
    .then(data => console.log(data))
    .catch(error => console.error('Error uploading the audio chunk:', error));
}

// Handle incoming messages
socket.on('transcript', message => {
    let item = document.createElement('li');
    item.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
    transcriptions.appendChild(item);
});
