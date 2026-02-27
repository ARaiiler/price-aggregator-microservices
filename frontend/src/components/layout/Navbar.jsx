import React from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useFavorites } from "../../context/FavoritesContext";

const Navbar = () => {
  const { user, logout } = useAuth();
  const { favorites } = useFavorites();
  const location = useLocation();

  const favoritesCount = favorites.length;
  const pathname = location.pathname;
  const showDashboardNav = pathname === "/dashboard" || pathname === "/favorites";

  return (
    <header className="sticky top-0 z-20 bg-white/95 backdrop-blur border-b border-gray-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14 sm:h-16">
        <Link
          to="/"
          className="flex items-center gap-2 text-gray-900 hover:text-primary transition-colors"
        >
          <span className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-sm">
            PC
          </span>
          <span className="font-semibold text-lg hidden sm:inline">
            PriceCompare
          </span>
        </Link>

        {showDashboardNav && (
          <nav className="flex items-center gap-2 sm:gap-3">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/favorites"
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-white"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              <span>Favorites</span>
              <span className="inline-flex items-center justify-center rounded-full bg-gray-100 text-gray-700 text-xs px-2 py-0.5 min-w-[1.5rem]">
                {favoritesCount}
              </span>
            </NavLink>
            {user?.email && (
              <span className="hidden md:inline text-sm text-gray-500 truncate max-w-[160px]">
                {user.email}
              </span>
            )}
            <button
              type="button"
              onClick={logout}
              className="px-3 py-2 rounded-lg text-sm font-medium text-white bg-red-500 hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </nav>
        )}
      </div>
    </header>
  );
};

export default Navbar;
