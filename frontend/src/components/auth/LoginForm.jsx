import React, { useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import Input from "../ui/Input";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import Alert from "../ui/Alert";

const LoginForm = () => {
  const { login, authLoading } = useAuth();
  const location = useLocation();
  const from = location.state?.from || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    try {
      await login(email.trim(), password);
    } catch (err) {
      setError(err?.message || "Invalid credentials. Please try again.");
    }
  };

  return (
    <div className="bg-white/90 border border-white rounded-2xl shadow-xl shadow-gray-200/80 backdrop-blur-sm p-6 sm:p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome back</h1>
      <p className="text-gray-600 text-sm mb-6 leading-relaxed">
        Log in to compare prices across your favorite stores.
      </p>
      {from && from !== "/dashboard" && (
        <p className="text-sm text-gray-600 mb-4 rounded-lg bg-gray-50 border border-gray-200 px-3 py-2">
          You need to be logged in to access{" "}
          <span className="font-medium text-primary">{from}</span>.
        </p>
      )}
      {error && (
        <div className="mb-4">
          <Alert type="error">{error}</Alert>
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <Input
          label="Email"
          name="email"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
        <Input
          label="Password"
          name="password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
        <Button type="submit" fullWidth disabled={authLoading}>
          {authLoading ? (
            <>
              <Spinner size="sm" /> Logging in...
            </>
          ) : (
            "Log in"
          )}
        </Button>
      </form>
    </div>
  );
};

export default LoginForm;
