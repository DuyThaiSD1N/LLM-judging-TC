// Load .env từ root hoặc callbot-api directory
const path = require('path');
require('dotenv').config({
    path: path.resolve(__dirname, '../../callbot-api/.env')
});

const express = require('express');
const cors = require('cors');

const uploadRoute = require('./routes/upload');
const runRoute = require('./routes/run');
const templateRoute = require('./routes/template');

const app = express();
const PORT = process.env.PORT || 8099;

// CORS config
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    credentials: true
}));

app.use(express.json());

// Serve static files với MIME type đúng
app.use(express.static(path.join(__dirname, '../testcase-form'), {
    setHeaders: (res, filePath) => {
        if (filePath.endsWith('.css')) {
            res.setHeader('Content-Type', 'text/css');
        } else if (filePath.endsWith('.js')) {
            res.setHeader('Content-Type', 'application/javascript');
        }
    }
}));

// API routes
app.use('/api', uploadRoute);
app.use('/api', runRoute);
app.use('/api', templateRoute);

// Health check endpoint cho Render
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Root endpoint
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../testcase-form/index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Server running on port ${PORT}`);
    console.log(`📍 Environment: ${process.env.NODE_ENV || 'development'}`);
});
