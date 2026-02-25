import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

// DEV: mettre à false quand tu auras le backend
const ALLOW_PUBLIC_ACCESS = true;

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (ALLOW_PUBLIC_ACCESS) {
    return <Outlet />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ from: location.pathname || "/" }}
        replace
      />
    );
  }

  return <Outlet />;
};

export default ProtectedRoute;

