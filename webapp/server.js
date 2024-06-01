const express = require('express');
const { createServer } = require('http');
const socketIo = require('socket.io');
const multer = require('multer');
const { spawn } = require('child_process');
const app = express();
const server = createServer(app);
const io = socketIo(server);

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, './uploads')
    },
    filename: function (req, file, cb) {
        cb(null, Date.now() + '-' + file.originalname)
    }
});
const upload = multer({ storage: storage });

app.use(express.static('public'));

app.post('/upload', upload.single('audioData'), (req, res) => {
    const filePath = req.file.path;
    const transcribeProcess = spawn('python', ['transcribe.py', filePath]);

    transcribeProcess.stdout.on('data', (data) => {
        const text = data.toString();
        const timestamp = new Date().toLocaleTimeString();
        io.emit('transcript', { text: text, timestamp: timestamp });
        res.send({ message: 'Transcription in progress', status: 'success' });
    });

    transcribeProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
        res.status(500).send({ error: 'Error during transcription' });
    });
});

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
