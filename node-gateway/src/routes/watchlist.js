const express = require('express');
const Watchlist = require('../models/Watchlist');
const router = express.Router();

// GET /watchlist
router.get('/', async (req, res) => {
    try {
        const items = await Watchlist.find({ user: req.user.userId })
        .sort({ addedAt: -1 });
        res.json(items);
    } catch (error) {
        res.status(500).json({ message: 'Failed to fetch watchlist' });
    }
});

// POST /watchlist
router.post('/', async (req, res) => {
    try {
        const { productId, productName, lastPrice, source, currency, productUrl, imageUrl } = req.body;

        if (!productId || !productName) {
        return res.status(400).json({ message: 'productId and productName are required' });
        }

        const exists = await Watchlist.findOne({ user: req.user.userId, productId });
        if (exists) {
        return res.status(400).json({ message: 'Product already in watchlist' });
        }

        const item = await Watchlist.create({
        user: req.user.userId,
        productId,
        productName,
        lastPrice,
        source,
        currency: currency || 'MAD',
        productUrl,
        imageUrl,
        });

        res.status(201).json(item);
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Failed to add to watchlist' });
    }
});

// DELETE /watchlist/:id
router.delete('/:id', async (req, res) => {
    try {
        const deleted = await Watchlist.findOneAndDelete({
        _id: req.params.id,
        user: req.user.userId,
        });

        if (!deleted) {
        return res.status(404).json({ message: 'Item not found' });
        }

        res.json({ message: 'Removed from watchlist' });
    } catch (error) {
        res.status(500).json({ message: 'Failed to remove from watchlist' });
    }
});

module.exports = router;