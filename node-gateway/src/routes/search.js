const express = require('express');
const axios = require('axios');
const { query, validationResult } = require('express-validator');

const router = express.Router();

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://python-collector:8000';

/**
 * @route   GET /search
 * @desc    Search for products via Python collector service
 * @access  Public (add JWT middleware for production)
 */
router.get(
  '/',
  [query('query').notEmpty().trim().escape()],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { query: searchQuery } = req.query;

    try {
      // Call Python collector service
      const response = await axios.post(
        `${PYTHON_SERVICE_URL}/internal/search`,
        { product_name: searchQuery },
        { timeout: 15000 }
      );

      res.json({
        success: true,
        query: searchQuery,
        results: response.data.results || [],
        cached: response.data.cached ?? false,
        sources_queried: response.data.sources_queried ?? 0,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Search error:', error.message);
      
      if (error.code === 'ECONNREFUSED') {
        return res.status(503).json({
          success: false,
          message: 'Product collector service unavailable',
          error: 'Service temporarily down'
        });
      }

      res.status(500).json({
        success: false,
        message: 'Failed to fetch products',
        error: error.message
      });
    }
  }
);

module.exports = router;
