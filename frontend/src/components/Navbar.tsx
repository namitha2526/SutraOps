import React, { useState, useEffect, useRef } from "react";
import { useStore } from "../store/useStore";
import { Bell, Shield, ChevronDown, CheckCircle2 } from "lucide-react";

export const Navbar: React.FC = () => {
  const { user, notifications, fetchNotifications } = useStore();
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchNotifications();
    // Refresh alerts periodically (e.g., every 30s)
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Handle clicking outside notifications dropdown to close it
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.length;

  return (
    <header className="h-16 border-b border-slate-800/60 flex items-center justify-between px-8 bg-slate-950/20 backdrop-blur-md sticky top-0 z-40 select-none">
      {/* Active Corporate Tenant Indicator */}
      <div className="flex items-center space-x-3">
        <Shield className="w-5 h-5 text-indigo-400" />
        <span className="text-sm font-semibold tracking-wide text-slate-200">
          SutraOps Corp Workspace
        </span>
        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          Active Workspace
        </span>
      </div>

      <div className="flex items-center space-x-6">
        {/* Real-time Alerts Bell dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900/60 transition-all duration-200 cursor-pointer relative"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-slate-950 animate-pulse-subtle"></span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 glass-panel border border-slate-800 rounded-2xl shadow-2xl glass-panel-glow overflow-hidden z-50">
              <div className="p-4 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-200">Pending Actions Feed</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400">
                  {unreadCount} alerts
                </span>
              </div>

              <div className="max-h-64 overflow-y-auto divide-y divide-slate-800/40">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-2">
                    <CheckCircle2 className="w-6 h-6 text-slate-600" />
                    <span>All clear! No pending step reviews assigned to your role context.</span>
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className="p-4 hover:bg-slate-900/40 transition-colors duration-150 flex flex-col space-y-1"
                    >
                      <span className="text-xs font-semibold text-slate-200">{notif.title}</span>
                      <span className="text-[11px] text-slate-400 leading-relaxed">{notif.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Vertical Separator */}
        <div className="h-6 w-px bg-slate-800"></div>

        {/* Quick User Identity badge */}
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <span className="block text-xs font-medium text-slate-300">
              {user?.full_name}
            </span>
            <span className="block text-[10px] text-indigo-400 font-bold uppercase tracking-wider">
              {user?.department?.code || "GENERAL"} DEPT
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-slate-850 border border-slate-700/60 flex items-center justify-center font-bold text-slate-300 text-xs">
            {user?.full_name.charAt(0)}
          </div>
        </div>
      </div>
    </header>
  );
};
export default Navbar;
