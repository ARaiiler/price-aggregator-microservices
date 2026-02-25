import React from "react";
import { Link } from "react-router-dom";
import LoginForm from "../components/auth/LoginForm";

const LoginPage = () => {
  return (
    <section className="py-6 sm:py-10">
      <div className="max-w-md mx-auto">
        <LoginForm />
        <p className="text-center text-sm text-gray-600 mt-6">
          Don&apos;t have an account?{" "}
          <Link to="/register" className="font-medium text-primary hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </section>
  );
};

export default LoginPage;
