import React from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import styles from "./Header.module.css";

const Header = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();

  const isAuthPage =
    location.pathname === "/login" || location.pathname === "/register";

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <Link to="/" className={styles.brand}>
          <span className={styles.logo}>PC</span>
          <div className={styles.brandText}>
            <span className={styles.title}>PriceCompare</span>
            <span className={styles.subtitle}>Smart price aggregator</span>
          </div>
        </Link>

        <nav className={styles.nav}>
          {isAuthenticated && (
            <>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  `${styles.link} ${isActive ? styles.linkActive : ""}`
                }
              >
                Dashboard
              </NavLink>
              <NavLink
                to="/search"
                className={({ isActive }) =>
                  `${styles.link} ${isActive ? styles.linkActive : ""}`
                }
              >
                Search
              </NavLink>
            </>
          )}
        </nav>

        <div className={styles.actions}>
          {isAuthenticated ? (
            <>
              {user?.email && (
                <span className={styles.userEmail}>{user.email}</span>
              )}
              <button type="button" className={styles.logoutBtn} onClick={logout}>
                Logout
              </button>
            </>
          ) : !isAuthPage ? (
            <>
              <Link to="/login" className={styles.loginBtn}>
                Log in
              </Link>
              <Link to="/register" className={styles.registerBtn}>
                Sign up
              </Link>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
};

export default Header;

