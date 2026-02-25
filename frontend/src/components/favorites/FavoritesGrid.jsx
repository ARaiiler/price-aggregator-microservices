import React from "react";
import ProductCard from "../search/ProductCard";
import { useFavorites, productId } from "../../context/FavoritesContext";

const FavoritesGrid = () => {
  const { favorites } = useFavorites();

  if (!favorites.length) {
    return (
      <div className="text-center py-14 px-6 rounded-2xl border border-dashed border-gray-300 bg-white/70">
        <p className="text-gray-700 text-lg font-medium mb-2">
          No favorites yet.
        </p>
        <p className="text-gray-500 text-sm">
          Click the heart icon on products to save them here.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
      {favorites.map((product, index) => (
        <ProductCard
          key={productId(product) || index}
          product={product}
        />
      ))}
    </div>
  );
};

export default FavoritesGrid;
