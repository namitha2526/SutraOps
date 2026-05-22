import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useStore } from "../store/useStore";
import { 
  LayoutDashboard, 
  KanbanSquare, 
  Store, 
  TrendingUp, 
  Settings, 
  LogOut, 
  Workflow
} from "lucide-react";

export const Sidebar: React.FC = () => {
  const { user, clearSession } = useStore();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearSession();
    navigate("/login");
  };

  const navItems = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Kanban Board", path: "/kanban", icon: KanbanSquare },
    { name: "Templates Store", path: "/templates", icon: Store },
    { name: "SLA Analytics", path: "/analytics", icon: TrendingUp },
  ];

  const isAdmin = user?.role === "Admin" || user?.role === "SuperAdmin";

  return (
    <div className="w-64 glass-panel border-r border-slate-800/80 min-h-screen flex flex-col justify-between select-none">
      <div>
        {/* Brand header */}
        <div className="p-6 border-b border-slate-800/60 flex items-center space-x-3">
          <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/30">
            <Workflow className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              NexusFlow
            </span>
            <span className="block text-[10px] text-indigo-400 uppercase tracking-widest font-bold">
              Enterprise
            </span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="p-4 space-y-1.5 mt-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-indigo-550/20 text-white border-l-2 border-indigo-500 glass-panel"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}

          {/* Conditional Administration Link */}
          {isAdmin && (
            <Link
              to="/admin"
              className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                location.pathname === "/admin"
                  ? "bg-indigo-550/20 text-white border-l-2 border-indigo-500 glass-panel"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              }`}
            >
              <Settings className={`w-4 h-4 ${location.pathname === "/admin" ? "text-indigo-400" : "text-slate-400"}`} />
              <span>Administration</span>
            </Link>
          )}
        </nav>
      </div>

      {/* Corporate profile and Sign out */}
      <div className="p-4 border-t border-slate-800/60">
        <div className="flex items-center space-x-3 p-3 bg-slate-900/50 rounded-xl border border-slate-800/30 mb-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-550 to-brand-500 flex items-center justify-center font-bold text-white text-sm">
            {user?.full_name.charAt(0)}
          </div>
          <div className="overflow-hidden">
            <span className="block text-xs font-semibold text-slate-200 truncate">
              {user?.full_name}
            </span>
            <span className="block text-[10px] text-indigo-400 uppercase font-bold">
              {user?.role}
            </span>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium text-rose-400 hover:text-rose-350 hover:bg-rose-500/10 transition-all duration-200 cursor-pointer"
        >
          <LogOut className="w-4 h-4 text-rose-400" />
          <span>Sign Out Session</span>
        </button>
      </div>
    </div>
  );
};
export default Sidebar;
