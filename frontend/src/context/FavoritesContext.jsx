import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

const FAVORITES_KEY = "favorites";

const getStoredFavorites = () => {
  try {
    const raw = localStorage.getItem(FAVORITES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

/** Stable id for a product (API may use name, price, source, url, currency, in_stock) */
export const productId = (product) => {
  if (!product) return "";
  const name = product.name || product.title || "";
  const source = product.source || product.vendor || product.store || "";
  const url = product.url || "";
  return `${name}|${source}|${url}`;
};

const FavoritesContext = createContext(null);

export const FavoritesProvider = ({ children }) => {
  const [favorites, setFavorites] = useState(getStoredFavorites);

  useEffect(() => {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
  }, [favorites]);

  const isFavorite = useCallback(
    (product) => {
      const id = productId(product);
      return favorites.some((p) => productId(p) === id);
    },
    [favorites]
  );

  const addToFavorites = useCallback((product) => {
    if (!product) return;
    setFavorites((prev) => {
      const id = productId(product);
      if (prev.some((p) => productId(p) === id)) return prev;
      const normalized = normalizeProduct(product);
      return [...prev, normalized];
    });
  }, []);

  const removeFromFavorites = useCallback((product) => {
    if (!product) return;
    const id = productId(product);
    setFavorites((prev) => prev.filter((p) => productId(p) !== id));
  }, []);

  const toggleFavorite = useCallback(
    (product) => {
      if (!product) return;
      if (isFavorite(product)) {
        removeFromFavorites(product);
      } else {
        addToFavorites(product);
      }
    },
    [isFavorite, addToFavorites, removeFromFavorites]
  );

  const value = {
    favorites,
    isFavorite,
    addToFavorites,
    removeFromFavorites,
    toggleFavorite,
  };

  return (
    <FavoritesContext.Provider value={value}>
      {children}
    </FavoritesContext.Provider>
  );
};

export const useFavorites = () => {
  const context = useContext(FavoritesContext);
  if (!context) {
    throw new Error("useFavorites must be used within a FavoritesProvider");
  }
  return context;
};

/** Normalize API product (e.g. in_stock) to a consistent shape for storage */
function normalizeProduct(p) {
  return {
    name: p.name || p.title || "Unnamed product",
    price: p.price ?? p.currentPrice ?? p.amount,
    source: p.source || p.vendor || p.store,
    url: p.url,
    currency: p.currency || "USD",
    in_stock: p.in_stock ?? p.inStock ?? true,
  };
}
