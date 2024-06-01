let socket = io();
let recorder, gumStream;
const recordButton = document.getElementById('recordButton');
const transcriptions = document.getElementById('transcriptions');

recordButton.addEventListener('click', () => {
    if (recorder && recorder.state === "recording") {
        recorder.stopRecording(() => {
            const blob = recorder.getBlob();
            sendData(blob);
            gumStream.getTracks().forEach(track => track.stop());
        });
        recorder = null;
        recordButton.textContent = "Record";
    } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            gumStream = stream;
            recorder = RecordRTC(stream, {
                type: 'audio',
                mimeType: 'audio/webm',
                timeSlice: 10000,
                ondataavailable: function(blob) {
                    sendData(blob);
                }
            });
            recorder.startRecording();
            recordButton.textContent = "Listening...";
        }).catch(err => console.error('An error occurred: ' + err));
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

// Dictionary to store transcription data by chunk_id
let transcriptionsData = {};

socket.on('transcript chunk', chunk => {
    if (!transcriptionsData[chunk.chunk_id]) {
        transcriptionsData[chunk.chunk_id] = {
            text: chunk.text,
            metadata: null
        };
        updateTranscriptionDisplay(chunk.chunk_id);
    } else {
        transcriptionsData[chunk.chunk_id].text += chunk.text;
    }
});

socket.on('transcription data', metadata => {
    metadata.forEach(meta => {
        if (transcriptionsData[meta.OriginalDetails.chunk_id]) {
            transcriptionsData[meta.OriginalDetails.chunk_id].metadata = meta;
            updateTranscriptionDisplay(meta.OriginalDetails.chunk_id);
        }
    });
});

function updateTranscriptionDisplay(chunkId) {
    const entry = transcriptionsData[chunkId];
    let item = document.createElement('div');
    item.classList.add('transcription-block');
    let text = entry.text;
    if (entry.metadata) {
        text = highlightText(entry.text, entry.metadata.OriginalDetails.from, entry.metadata.OriginalDetails.to);
    }

    item.innerHTML = `
        <p>Chunk ID: ${chunkId}</p>
        <p>${text}</p>
        <p>Status: ${entry.metadata ? entry.metadata.Status : 'Pending'}</p>
        <p>Summary: ${entry.metadata ? entry.metadata.summary : 'N/A'}</p>
        <p>Citation: ${entry.metadata ? `<a href='${entry.metadata.Citation.Link}'>${entry.metadata.Citation.Summary}</a> - Source: ${entry.metadata.Citation.Source}` : 'N/A'}</p>
    `;
    // Check if this chunk is already displayed
    const existingElement = document.getElementById(`chunk-${chunkId}`);
    if (existingElement) {
        transcriptions.replaceChild(item, existingElement);
    } else {
        item.id = `chunk-${chunkId}`;
        transcriptions.insertBefore(item, transcriptions.firstChild); // Prepend new items to keep the latest at the top
    }
}

function highlightText(text, from, to) {
    const startText = text.substring(0, from);
    const highlight = text.substring(from, to);
    const endText = text.substring(to);
    return `${startText}<span style="background-color: yellow;">${highlight}</span>${endText}`;
}
