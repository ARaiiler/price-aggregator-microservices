import React from "react";
import FavoritesGrid from "../components/favorites/FavoritesGrid";

const FavoritesPage = () => {
  return (
    <section className="max-w-5xl mx-auto space-y-6">
      <header className="rounded-2xl border border-white/70 bg-white/85 backdrop-blur-md shadow-lg shadow-gray-200/70 p-5 sm:p-6">
        <p className="text-xs font-medium uppercase tracking-wide text-gray-500 mb-1">Collection</p>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          Your Favorite Products
        </h1>
        <p className="text-gray-600 text-sm">
          Products you saved with the heart icon. They persist after refresh.
        </p>
      </header>
      <FavoritesGrid />
    </section>
  );
};

export default FavoritesPage;
