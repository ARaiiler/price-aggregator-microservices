import React from "react";

const SkeletonCard = () => (
  <div className="bg-white rounded-lg shadow p-5 animate-pulse">
    <div className="flex justify-between items-start mb-3">
      <div className="h-5 bg-gray-200 rounded w-3/4" />
      <div className="h-5 w-5 bg-gray-200 rounded" />
    </div>
    <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
    <div className="flex justify-between items-center mb-3">
      <div className="h-6 bg-gray-200 rounded w-24" />
      <div className="h-5 bg-gray-200 rounded w-20" />
    </div>
    <div className="h-10 bg-gray-200 rounded w-full" />
  </div>
);

const LoadingSkeleton = ({ count = 6 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
};

export default LoadingSkeleton;
