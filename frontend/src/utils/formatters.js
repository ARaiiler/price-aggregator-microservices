export const formatCurrency = (value, currency = "USD", locale = "en-US") => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(Number(value));
  } catch {
    return `${value} ${currency}`;
  }
};

export const formatSource = (source) => {
  if (!source) return "Unknown";
  return String(source)
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

export const formatStockStatus = (inStock) => {
  if (typeof inStock === "boolean") {
    return inStock ? "In Stock" : "Out of Stock";
  }
  if (typeof inStock === "string") {
    return inStock;
  }
  return "Check availability";
};

