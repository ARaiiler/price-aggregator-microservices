const mongoose = require('mongoose');

const SearchHistorySchema = new mongoose.Schema(
    {
        userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
        },

        query: {
        type: String,
        required: true
        },

        providers: {
        type: [String],
        default: []
        },

        resultCount: {
        type: Number,
        default: 0
        }
    },
    {
        timestamps: true
    }
);

module.exports = mongoose.model('SearchHistory', SearchHistorySchema);