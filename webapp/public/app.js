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
    // .then(data => console.log(data))
    .catch(error => console.error('Error uploading the audio chunk:', error));
}

let transcriptionsData = {}; // Stores all transcription data by chunk_id

socket.on('transcript_chunk', chunk => {
    // console.log('transciption chunk', chunk)
    transcriptionsData[chunk.chunk_id] = transcriptionsData[chunk.chunk_id] || { text: '', metadata: null };
    transcriptionsData[chunk.chunk_id].text += chunk.text;
    renderAllTranscriptions(); // Re-render all transcriptions upon receiving a new chunk
});

socket.on('meta', metadata => {
    // console.log('metadata', metadata)
    // console.log('transcriptionsData', transcriptionsData)
    metadata.forEach(meta => {
        if (!transcriptionsData[meta.OriginalDetails.chunk_id]) {
            transcriptionsData[meta.OriginalDetails.chunk_id] = {}
        }
        // console.log("meta arrived:" + meta);
        transcriptionsData[meta.OriginalDetails.chunk_id].metadata = meta;
    });
    renderAllTranscriptions(); // Re-render all transcriptions upon metadata update
});

let totalScore = 0

function getScoreFromStatus(status) {
    switch (status) {
        case 'ACCURATE':
            return 5
            break;
        case 'PARTIALLY ACCURATE':
            return -1
            break;
        case 'NOT ACCURATE':
            return -5
            break;
        default:
            0
    }
}

function renderAllTranscriptions() {
    // console.log(transcriptionsData)
    transcriptions.innerHTML = ''; // Clear the existing transcriptions
    totalScore = 0
    Object.keys(transcriptionsData).sort((a, b) => a - b).forEach(chunkId => {
        const entry = transcriptionsData[chunkId];
        if (entry && entry.metadata&& entry.metadata.Status) {
            totalScore += getScoreFromStatus(entry.metadata.Status)
        }
        const item = createTranscriptionElement(chunkId, entry);
        transcriptions.appendChild(item); // Append items in ascending order by chunk ID
    });
    console.log('totalScore', totalScore)
}

function createTranscriptionElement(chunkId, entry) {
    let item = document.createElement('div');
    item.classList.add('transcription-block');
    item.id = `chunk-${chunkId}`;
    let text = entry.text;
    let color = 'yellow'; // Default highlight color

    if (entry.metadata) {
        switch (entry.metadata.Status) {
            case 'ACCURATE':
                color = 'green';
                break;
            case 'PARTIALLY ACCURATE':
                color = 'orange';
                break;
            case 'NOT ACCURATE':
                color = 'red';
                break;
            default:
                color = 'grey'; // For undefined status
        }
        text = highlightText(text, entry.metadata.OriginalDetails.from, entry.metadata.OriginalDetails.to, color);
    }

    item.innerHTML = `
        <p>Chunk ID: ${chunkId}</p>
        <p>${text}</p>
        <p>Status: ${entry.metadata ? entry.metadata.Status : 'Pending'}</p>
        <p>Summary: ${entry.metadata ? entry.metadata.summary : 'N/A'}</p>
        <p>Citation: ${entry.metadata ? `<a href='${entry.metadata.Citation.Link}'>${entry.metadata.Citation.Summary}</a> - Source: ${entry.metadata.Citation.Source}` : 'N/A'}</p>
    `;
    return item;
}

function highlightText(text, from, to, color) {
    if (!text) return
    // console.log(text, from, to, color)
    const startText = text.substring(0, from);
    const highlighted = text.substring(from, to);
    const endText = text.substring(to);
    return `${startText}<span style="background-color: ${color};">${highlighted}</span>${endText}`;
}
