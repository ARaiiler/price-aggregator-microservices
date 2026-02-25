import React from "react";

const Button = ({
  children,
  variant = "primary",
  fullWidth = false,
  className = "",
  disabled,
  ...props
}) => {
  const base =
    "inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-70 disabled:cursor-not-allowed";
  const variants = {
    primary:
      "bg-primary text-white hover:bg-primary-hover focus:ring-primary shadow-sm",
    secondary:
      "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-400",
    ghost:
      "bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-400",
  };
  const width = fullWidth ? "w-full" : "";
  const classes = [base, variants[variant] || variants.primary, width, className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} disabled={disabled} {...props}>
      {children}
    </button>
  );
};

export default Button;
