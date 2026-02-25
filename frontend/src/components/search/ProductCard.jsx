import React from "react";
import { FiHeart } from "react-icons/fi";
import { FaHeart } from "react-icons/fa";
import { useFavorites } from "../../context/FavoritesContext";
import { formatCurrency, formatSource, formatStockStatus } from "../../utils/formatters";

const ProductCard = ({ product }) => {
  const { isFavorite, toggleFavorite } = useFavorites();

  if (!product) return null;

  const name = product.name || product.title || "Unnamed product";
  const price = product.price ?? product.currentPrice ?? product.amount;
  const currency = product.currency || "USD";
  const source = product.source || product.vendor || product.store;
  const inStock = product.in_stock ?? product.inStock ?? true;
  const stockLabel = formatStockStatus(inStock);
  const isOut = String(stockLabel).toLowerCase().includes("out");

  const favorited = isFavorite(product);

  return (
    <article className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-gray-100 bg-white/80 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-lg">
      {/* Top accent bar */}
      <div className="h-1 w-full bg-gradient-to-r from-primary to-teal" />

      <div className="flex flex-1 flex-col p-4 sm:p-5 gap-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400 mb-1">
              {formatSource(source)}
            </p>
            <h3 className="text-sm sm:text-base font-semibold text-gray-900 leading-snug line-clamp-2">
              {name}
            </h3>
          </div>
          <button
            type="button"
            onClick={() => toggleFavorite(product)}
            className="flex-shrink-0 rounded-full bg-gray-50 p-1.5 text-gray-400 shadow-sm transition group-hover:bg-red-50 group-hover:text-heart focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            aria-label={favorited ? "Remove from favorites" : "Add to favorites"}
          >
            {favorited ? (
              <FaHeart className="h-5 w-5 text-heart" aria-hidden />
            ) : (
              <FiHeart className="h-5 w-5" aria-hidden />
            )}
          </button>
        </div>

        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-xs text-gray-400 mb-0.5">Price</p>
            <p className="text-xl font-semibold text-gray-900">
              {formatCurrency(price, currency)}
            </p>
          </div>
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${
              isOut
                ? "bg-red-50 text-red-700 ring-1 ring-red-100"
                : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100"
            }`}
          >
            {stockLabel}
          </span>
        </div>

        {product.url && (
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-auto inline-flex items-center justify-center rounded-xl border border-primary/10 bg-primary/90 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-primary hover:shadow-md"
          >
            View Deal
          </a>
        )}
      </div>
    </article>
  );
};

export default ProductCard;
