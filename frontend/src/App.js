import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_URL}/search`, {
        params: { query: searchQuery }
      });
      setResults(response.data.results || []);
    } catch (err) {
      setError('Failed to fetch results. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Price Aggregator</h1>
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search for products..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="search-button" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </header>

      <main className="results-container">
        {error && <div className="error-message">{error}</div>}
        
        {results.length > 0 && (
          <div className="results">
            {results.map((item, index) => (
              <div key={index} className="result-card">
                <h3>{item.name}</h3>
                <p className="price">${item.price}</p>
                <p className="source">Source: {item.source}</p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
