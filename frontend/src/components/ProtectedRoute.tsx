import React, { useEffect } from "react";
import { Navigate } from "react-router-dom";
import { useStore } from "../store/useStore";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loadUserProfile, clearSession } = useStore();
  const token = localStorage.getItem("access_token");

  useEffect(() => {
    if (token && !user) {
      loadUserProfile().catch(() => {
        clearSession();
      });
    }
  }, [token, user, loadUserProfile, clearSession]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-4">
        {/* Modern premium glassmorphic loading spinner */}
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-slate-800"></div>
          <div className="absolute inset-0 rounded-full border-4 border-t-indigo-500 border-r-indigo-500 animate-spin"></div>
        </div>
        <p className="text-slate-400 text-sm font-medium tracking-wide animate-pulse">
          Resolving secure tenant gateway credentials...
        </p>
      </div>
    );
  }

  return <>{children}</>;
};
export default ProtectedRoute;
