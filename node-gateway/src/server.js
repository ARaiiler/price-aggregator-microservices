const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const connectDatabase = require('./config/database');
const authMiddleware = require('./middleware/auth');

const authRoutes = require('./routes/auth');
const searchRoutes = require('./routes/search');
const healthRoutes = require('./routes/health');
const watchlistRoutes = require('./routes/watchlist');

const app = express();
const PORT = process.env.PORT || 5000;

// 🔐 Security middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));

// 📦 Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use('/health', healthRoutes);
app.use('/auth', authRoutes);
app.use('/search', authMiddleware, searchRoutes);
app.use('/watchlist', authMiddleware, watchlistRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Node Gateway',
    version: '1.0.0',
    status: 'running'
  });
});

// ❌ 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: {
      message: 'Route not found',
      status: 404
    }
  });
});

// 🔥 Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({
    error: {
      message: err.message || 'Internal Server Error',
      status: err.status || 500
    }
  });
});

// 🚀 Start server after DB connection
(async () => {
  try {
    await connectDatabase();
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`🚀 Node Gateway running on port ${PORT}`);
      console.log(`📡 Environment: ${process.env.NODE_ENV || 'development'}`);
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
})();

module.exports = app;