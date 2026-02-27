const mongoose = require('mongoose');

const WatchlistSchema = new mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    productId:   { type: String, required: true },
    productName: { type: String, required: true },
    productUrl:  { type: String },
    imageUrl:    { type: String },
    source:      { type: String },
    lastPrice:   { type: Number },
    currency:    { type: String, default: 'MAD' },
    addedAt:     { type: Date, default: Date.now },
});

// Index pour éviter les doublons par user+productId
WatchlistSchema.index({ user: 1, productId: 1 }, { unique: true });

module.exports = mongoose.model('Watchlist', WatchlistSchema);