import React from "react";
import ProductCard from "./ProductCard";
import { productId } from "../../context/FavoritesContext";

const ProductGrid = ({ products = [] }) => {
  if (!products.length) {
    return (
      <p className="text-gray-500 text-center py-8">
        No results found. Try another keyword or check spelling.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
      {products.map((product, index) => (
        <ProductCard
          key={productId(product) || index}
          product={product}
        />
      ))}
    </div>
  );
};

export default ProductGrid;
