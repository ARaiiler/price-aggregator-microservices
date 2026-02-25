import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Button from "../components/ui/Button";

const LandingPage = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handlePrimary = () => {
    navigate(isAuthenticated ? "/dashboard" : "/register");
  };

  const handleSecondary = () => {
    navigate("/login");
  };

  return (
    <section className="py-6 sm:py-10">
      <div className="max-w-5xl mx-auto">
        <div className="rounded-3xl border border-white/70 bg-white/80 backdrop-blur-md shadow-xl shadow-gray-200/60 p-6 sm:p-10 text-center">
          <p className="inline-flex items-center rounded-full bg-primary/10 text-primary text-xs font-semibold px-3 py-1 mb-4">
            Smart shopping assistant
          </p>
          <h1 className="text-3xl sm:text-5xl font-bold text-gray-900 mb-4 leading-tight">
            Compare prices across stores in{" "}
            <span className="text-primary">seconds</span>
          </h1>
          <p className="text-gray-600 text-base sm:text-lg mb-8 max-w-2xl mx-auto">
            One search, all the prices. Find the best offer for your next
            purchase without opening dozens of tabs.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-10">
            <Button onClick={handlePrimary}>
              {isAuthenticated ? "Go to dashboard" : "Get started"}
            </Button>
            {!isAuthenticated && (
              <Button variant="secondary" onClick={handleSecondary}>
                I already have an account
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 text-left">
            <div className="rounded-2xl bg-gray-50 border border-gray-100 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Fast search</p>
              <p className="text-sm text-gray-700">Find product offers from multiple sources with a single query.</p>
            </div>
            <div className="rounded-2xl bg-gray-50 border border-gray-100 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Best offer</p>
              <p className="text-sm text-gray-700">Spot price differences instantly and choose the right store.</p>
            </div>
            <div className="rounded-2xl bg-gray-50 border border-gray-100 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Save favorites</p>
              <p className="text-sm text-gray-700">Keep products in your favorites and revisit them anytime.</p>
            </div>
          </div>
        </div>

      </div>

      <footer className="mt-16 pt-8 border-t border-gray-200 text-center text-xs text-gray-400">
        <p>© {new Date().getFullYear()} PriceCompare.</p>
      </footer>
    </section>
  );
};

export default LandingPage;
