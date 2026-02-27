const mongoose = require('mongoose');

/**
 * Connect to MongoDB
 * Uses MONGO_URI from environment variables
 */
const connectDatabase = async () => {
  try {
    const mongoUri = process.env.MONGO_URI;

    if (!mongoUri) {
      throw new Error('MONGO_URI is not defined in environment variables');
    }

    await mongoose.connect(mongoUri, {
        serverSelectionTimeoutMS: 5000
    });

    console.log('✅ Connected to MongoDB');

    // Optional: log when connection is lost
    mongoose.connection.on('disconnected', () => {
      console.warn('⚠️ MongoDB disconnected');
    });

    mongoose.connection.on('error', (err) => {
      console.error('❌ MongoDB connection error:', err);
    });

  } catch (error) {
    console.error('❌ Failed to connect to MongoDB:', error.message);
    process.exit(1); // Stop the app if DB connection fails
  }
};

module.exports = connectDatabase;