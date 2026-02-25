import React, { createContext, useContext, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { loginUser, registerUser } from "../services/api";

const AuthContext = createContext(null);

const TOKEN_KEY = "token";
const USER_KEY = "user";

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [authLoading, setAuthLoading] = useState(false);

  const persistAuth = useCallback((jwtToken, userInfo) => {
    setToken(jwtToken);
    setUser(userInfo);
    localStorage.setItem(TOKEN_KEY, jwtToken);
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
  }, []);

  const clearAuth = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    navigate("/", { replace: true });
  }, [clearAuth, navigate]);

  const login = async (email, password) => {
    setAuthLoading(true);
    try {
      const data = await loginUser(email, password);
      const jwtToken = data.token;
      const userInfo = { email };
      persistAuth(jwtToken, userInfo);
      navigate("/dashboard", { replace: true });
      return data;
    } catch (error) {
      throw error;
    } finally {
      setAuthLoading(false);
    }
  };

  const register = async (email, password) => {
    setAuthLoading(true);
    try {
      await registerUser(email, password);
      await login(email, password);
    } catch (error) {
      throw error;
    } finally {
      setAuthLoading(false);
    }
  };

  const value = {
    token,
    user,
    isAuthenticated: Boolean(token),
    authLoading,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
