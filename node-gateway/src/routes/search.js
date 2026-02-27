const express = require('express');
const { query, validationResult } = require('express-validator');
const { searchProducts } = require('../services/pythonService');
const SearchHistory = require('../models/SearchHistory');

const router = express.Router();

/**
 * GET /search?query=laptop
 * 🔐 JWT déjà appliqué dans server.js
 */
router.get(
  '/',
  [query('query').notEmpty().withMessage('Query is required')],
  async (req, res) => {

    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const searchQuery = req.query.query;

    try {
      // ✅ Appel correct vers Python via pythonService
      const data = await searchProducts(searchQuery);

      // ✅ Sauvegarder dans SearchHistory (optionnel mais bien)
      try {
        await SearchHistory.create({
          userId: req.user.userId,
          query: searchQuery,
          providers: data.sources || [],
          resultCount: data.total_results || 0,
        });
      } catch (histErr) {
        console.warn('SearchHistory save failed:', histErr.message);
      }

      res.status(200).json({
        success: true,
        query: searchQuery,
        results: data.results || [],
        sources: data.sources || [],
        total_results: data.total_results || 0,
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      console.error('Python service error:', error.message);
      res.status(503).json({
        success: false,
        message: 'Product collector service unavailable',
      });
    }
  }
);

module.exports = router;