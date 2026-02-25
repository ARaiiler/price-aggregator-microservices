import React, { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import Input from "../ui/Input";
import Button from "../ui/Button";
import Spinner from "../ui/Spinner";
import Alert from "../ui/Alert";

const RegisterForm = () => {
  const { register, authLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!email || !password || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    try {
      await register(email.trim(), password);
    } catch (err) {
      setError(err?.message || "Unable to register. Please try again.");
    }
  };

  return (
    <div className="bg-white/90 border border-white rounded-2xl shadow-xl shadow-gray-200/80 backdrop-blur-sm p-6 sm:p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Create your account</h1>
      <p className="text-gray-600 text-sm mb-6 leading-relaxed">
        Sign up to start tracking and comparing product prices.
      </p>
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
          placeholder="At least 6 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
        <Input
          label="Confirm password"
          name="confirmPassword"
          type="password"
          placeholder="Repeat your password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          autoComplete="new-password"
        />
        <Button type="submit" fullWidth disabled={authLoading}>
          {authLoading ? (
            <>
              <Spinner size="sm" /> Creating account...
            </>
          ) : (
            "Register"
          )}
        </Button>
      </form>
    </div>
  );
};

export default RegisterForm;
