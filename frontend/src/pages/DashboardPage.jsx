import React, { useState, useCallback } from "react";
import { FiUser, FiSearch } from "react-icons/fi";
import { useAuth } from "../context/AuthContext";
import { useFavorites } from "../context/FavoritesContext";
import { searchProducts } from "../services/api";
import ProductGrid from "../components/search/ProductGrid";
import LoadingSkeleton from "../components/search/LoadingSkeleton";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";

const DashboardPage = () => {
  const { user } = useAuth();
  const { favorites } = useFavorites();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = useCallback(async (searchTerm) => {
    setQuery(searchTerm);
    setError("");
    setLoading(true);
    try {
      const data = await searchProducts(searchTerm);
      const items = Array.isArray(data)
        ? data
        : data?.results || data?.items || [];
      setResults(Array.isArray(items) ? items : []);
    } catch (err) {
      console.error(err);
      setResults([]);
      setError(
        "Le serveur n'est pas encore disponible. Les résultats ne peuvent pas être affichés pour le moment."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    handleSearch(trimmed);
  };

  return (
    <section className="max-w-5xl mx-auto space-y-6">
      <div className="rounded-2xl border border-white/70 bg-white/85 backdrop-blur-md shadow-lg shadow-gray-200/70 px-5 sm:px-6 py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500 mb-1">Dashboard</p>
          <h1 className="text-2xl font-semibold text-gray-900">Price Aggregator</h1>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <FiUser className="w-5 h-5" />
          {user?.email && (
            <span className="text-sm truncate max-w-[160px]">
              {user.email}
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 sm:p-6">
        <p className="text-sm text-gray-500 mb-4 font-medium">
          Dashboard · Search to compare prices across sources
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Tapez le nom du produit..."
              className="w-full px-4 py-3.5 pr-10 rounded-xl border border-gray-300 bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent shadow-sm"
            />
            <FiSearch className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          </div>
          <Button type="submit" fullWidth disabled={loading}>
            {loading ? "Recherche..." : "Search"}
          </Button>
        </form>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 text-center">
          <p className="text-sm text-gray-500 mb-1 font-medium">Résultats de recherche</p>
          <p className="text-2xl font-semibold text-gray-900">
            {results.length}
          </p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 text-center">
          <p className="text-sm text-gray-500 mb-1 font-medium">Favoris</p>
          <p className="text-2xl font-semibold text-gray-900">
            {favorites.length}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 sm:p-6">
        {error && (
          <div className="mb-4">
            <Alert type="info">{error}</Alert>
          </div>
        )}

        {loading && <LoadingSkeleton count={6} />}

        {!loading && results.length === 0 && (
          <div className="flex items-center justify-center py-14">
            <p className="text-gray-500 text-center">
              Aucun résultat affiché. Lancez une recherche.
            </p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="-mx-1 sm:mx-0">
            <ProductGrid products={results} />
          </div>
        )}
      </div>
    </section>
  );
};

export default DashboardPage;
