import React from "react";

const typeClasses = {
  error: "bg-red-50 border-red-200 text-red-800",
  success: "bg-green-50 border-green-200 text-green-800",
  info: "bg-blue-50 border-blue-200 text-blue-800",
};

const Alert = ({ type = "error", title, children }) => {
  const classes = typeClasses[type] || typeClasses.error;
  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm ${classes}`}
      role="alert"
    >
      {title && <strong className="font-semibold block mb-1">{title}</strong>}
      {children && <span>{children}</span>}
    </div>
  );
};

export default Alert;
