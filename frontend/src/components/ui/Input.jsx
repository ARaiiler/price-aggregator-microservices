import React from "react";

const Input = ({ label, id, error, helperText, type = "text", className = "", ...props }) => {
  const inputId = id || props.name;
  const inputClasses =
    "w-full px-4 py-2.5 rounded-lg border bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-shadow " +
    (error
      ? "border-red-500 focus:ring-red-500"
      : "border-gray-300");

  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label
          className="block text-sm font-medium text-gray-700 mb-1"
          htmlFor={inputId}
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        className={inputClasses}
        {...props}
      />
      {helperText && !error && (
        <p className="mt-1 text-xs text-gray-500">{helperText}</p>
      )}
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};

export default Input;
