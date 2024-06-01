const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Set up a folder for storing audio files
const storage = multer.diskStorage({
    destination: './audio',
    filename: function(req, file, cb) {
        cb(null, 'audio-' + Date.now() + path.extname(file.originalname));
    }
});
const upload = multer({ storage: storage });

app.use(express.static('public'));  // Serve static files from 'public' directory

// Route for uploading audio and processing transcription
app.post('/upload', upload.single('audioData'), (req, res) => {
    res.status(200).send('Audio saved');
    // Add any required logic for processing audio here
});

// Socket connection
io.on('connection', (socket) => {
    console.log('A user connected');
    sendTranscriptChunks(socket);

    sendTranscriptionMetaData(socket);

    socket.on('disconnect', () => {
        console.log('User disconnected');
    });
});
function sendTranscriptionMetaData(socket) {
    const transcriptionData = [
        {
            "Status": "ACCURATE",
            "summary": "dad mother lunch",
            "OriginalDetails": {
                "chunk_id": 0,
                "text": "My dad's mother had just the largest hunch in her back",
                "from": 298,
                "to": 349
            },
            "Citation": {
                "Source": "MedlinePlus",
                "Summary": "Overview of lactose intolerance",
                "Link": "https://medlineplus.gov/lactoseintolerance.html"
            }
        }
    ];

    // Emit the structured data to the client
    socket.emit('transcription data', transcriptionData);
}
function sendTranscriptChunks(socket) {
    fs.readFile('sample_transciption.txt', 'utf8', (err, data) => {
        if (err) {
            console.error('Error reading file:', err);
            return;
        }
        const lines = data.split('\n');
        let index = 0;
        let chunkId = 0; // Initialize chunkId to keep track of the chunks

        const intervalId = setInterval(() => {
            if (index >= lines.length) {
                clearInterval(intervalId);
                socket.emit('transcript end', { message: 'All data sent.' });
                return;
            }
            const chunk = lines.slice(index, index + 10).join('\n');
            socket.emit('transcript chunk', {
                chunk_id: chunkId,
                text: chunk
            });
            index += 10;
            chunkId++; // Increment chunkId for each new chunk
        }, 10000); // Send every 10 seconds
    });
}


const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
