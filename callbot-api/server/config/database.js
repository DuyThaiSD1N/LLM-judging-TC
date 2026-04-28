// config/database.js — MongoDB connection

const mongoose = require('mongoose');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/callbot-testcase';

async function connectDB() {
    try {
        await mongoose.connect(MONGODB_URI);
        console.log('✅ MongoDB connected:', mongoose.connection.name);
    } catch (error) {
        console.error('❌ MongoDB connection error:', error.message);
        // Không throw error, cho phép app chạy mà không có DB (fallback to memory)
        console.warn('⚠️  Running without database - data will not persist');
    }
}

// Graceful shutdown
process.on('SIGINT', async () => {
    await mongoose.connection.close();
    console.log('MongoDB connection closed');
    process.exit(0);
});

module.exports = { connectDB };
