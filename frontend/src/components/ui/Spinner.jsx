import React from "react";

const sizeClasses = {
  sm: "w-4 h-4 border-2",
  md: "w-5 h-5 border-2",
  lg: "w-8 h-8 border-2",
};

const Spinner = ({ size = "md" }) => {
  const sizeClass = sizeClasses[size] || sizeClasses.md;
  return (
    <span
      className={`inline-block rounded-full border-gray-300 border-t-primary animate-spin ${sizeClass}`}
      aria-label="Loading"
    />
  );
};

export default Spinner;
