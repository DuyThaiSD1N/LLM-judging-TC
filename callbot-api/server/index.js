require('dotenv').config({ path: '../.env' });

const express = require('express');
const cors = require('cors');
const path = require('path');

const uploadRoute = require('./routes/upload');
const runRoute = require('./routes/run');
const templateRoute = require('./routes/template');

const app = express();
const PORT = process.env.PORT || 8099;

// CORS config cho Railway
app.use(cors({
    origin: '*', // Cho phép mọi origin, hoặc chỉ định domain cụ thể
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    credentials: true
}));

app.use(express.json());

// Serve static files
app.use(express.static(path.join(__dirname, '../testcase-form')));

// API routes
app.use('/api', uploadRoute);
app.use('/api', runRoute);
app.use('/api', templateRoute);

// Health check endpoint cho Railway
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
