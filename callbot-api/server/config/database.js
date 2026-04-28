// config/database.js — MongoDB connection

const mongoose = require('mongoose');

const MONGODB_URI = process.env.MONGODB_URI;

async function connectDB() {
    if (!MONGODB_URI) {
        console.warn('⚠️  MONGODB_URI not set - running without database');
        console.warn('⚠️  Data will not persist. Set MONGODB_URI to enable database.');
        return;
    }

    try {
        await mongoose.connect(MONGODB_URI);
        console.log('✅ MongoDB connected:', mongoose.connection.name);
    } catch (error) {
        console.error('❌ MongoDB connection error:', error.message);
        console.warn('⚠️  Running without database - data will not persist');
    }
}

// Graceful shutdown
process.on('SIGINT', async () => {
    if (mongoose.connection.readyState === 1) {
        await mongoose.connection.close();
        console.log('MongoDB connection closed');
    }
    process.exit(0);
});

module.exports = { connectDB };
