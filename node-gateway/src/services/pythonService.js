const axios = require('axios');

const pythonClient = axios.create({
  baseURL: process.env.PYTHON_SERVICE_URL,
  headers: {
    'X-Internal-Api-Key': process.env.INTERNAL_API_KEY,
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 secondes
});

/**
 * Rechercher des produits via le service Python
 * Retourne un tableau de Product normalisés en MAD
 */
const searchProducts = async (query) => {
  const response = await pythonClient.get('/api/search', {
    params: { q: query },
  });
  return response.data; // { success, query, results, total_results, sources, timestamp }
};

/**
 * Récupérer l'historique de prix d'un produit
 */
const getPriceHistory = async (productName, limit = 50) => {
  const response = await pythonClient.get(
    `/api/product/${encodeURIComponent(productName)}/history`,
    { params: { limit } }
  );
  return response.data; // { success, product_name, history, total_points }
};

/**
 * Récupérer les taux de change actuels
 */
const getCurrencyRates = async () => {
  const response = await pythonClient.get('/api/currencies');
  return response.data; // { base, rates, updated_at }
};

module.exports = { searchProducts, getPriceHistory, getCurrencyRates };