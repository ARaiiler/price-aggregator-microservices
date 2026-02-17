const express = require('express');
const router = express.Router();

/**
 * Health check endpoint
 * Returns service status and basic info
 */
router.get('/', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    service: 'node-gateway',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development'
  });
});

module.exports = router;
