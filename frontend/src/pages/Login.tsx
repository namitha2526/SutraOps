import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../store/useStore";
import { api } from "../services/api";
import { Shield, Sparkles, Building2, User, Key, Mail, Lock } from "lucide-react";

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { setSession, loadUserProfile } = useStore();
  const [activeTab, setActiveTab] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sign In inputs
  const [loginEmail, setLoginEmail] = useState("admin@sutraops.com"); // Pre-populated seed defaults
  const [loginPassword, setLoginPassword] = useState("password123");

  // Register Tenant inputs
  const [orgName, setOrgName] = useState("");
  const [orgDomain, setOrgDomain] = useState("");
  const [adminName, setAdminName] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post("/auth/login", {
        email: loginEmail,
        password: loginPassword,
      });

      const { access_token, refresh_token } = response.data;
      
      // Seed fallback organization ID or parse from profile
      setSession(access_token, refresh_token, "");
      await loadUserProfile();
      
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.message || "Invalid corporate credentials");
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post("/auth/register", {
        organization_name: orgName,
        domain: orgDomain,
        admin_name: adminName,
        admin_email: adminEmail,
        admin_password: adminPassword,
      });

      // Automatically sign in with newly created administrator account
      const loginResponse = await api.post("/auth/login", {
        email: adminEmail,
        password: adminPassword,
      });

      const { access_token, refresh_token } = loginResponse.data;
      setSession(access_token, refresh_token, response.data.organization_id);
      await loadUserProfile();

      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.message || "Tenant onboarding failed. Check fields.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 relative overflow-hidden select-none">
      {/* Decorative ambient background glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-brand-500/10 blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md glass-panel border border-slate-800/80 rounded-3xl shadow-2xl p-8 relative z-10 glass-panel-glow">
        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-indigo-500/10 rounded-2xl border border-indigo-500/20 mb-4 animate-pulse-subtle">
            <Shield className="w-8 h-8 text-indigo-400" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">NexusFlow</h1>
          <p className="text-sm text-slate-400 mt-1">Enterprise Automation Portal Gateway</p>
        </div>

        {/* Tab triggers */}
        <div className="grid grid-cols-2 p-1 bg-slate-900/60 rounded-xl border border-slate-800/60 mb-6">
          <button
            onClick={() => { setActiveTab("login"); setError(null); }}
            className={`py-2 rounded-lg text-xs font-semibold tracking-wide transition-all cursor-pointer ${
              activeTab === "login"
                ? "bg-indigo-500 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => { setActiveTab("register"); setError(null); }}
            className={`py-2 rounded-lg text-xs font-semibold tracking-wide transition-all cursor-pointer ${
              activeTab === "register"
                ? "bg-indigo-500 text-white shadow-lg"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Register Org
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold leading-relaxed">
            {error}
          </div>
        )}

        {/* FORMS */}
        {activeTab === "login" ? (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Corporate Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full bg-slate-900/40 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="name@company.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Secure Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full bg-slate-900/40 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-550 hover:bg-indigo-500 disabled:bg-indigo-850 text-white font-semibold text-xs tracking-wider py-3 rounded-xl transition-all cursor-pointer shadow-lg shadow-indigo-950/45 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <span className="w-4 h-4 rounded-full border-2 border-slate-300 border-t-transparent animate-spin"></span>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Authenticate Securely</span>
                </>
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRegisterSubmit} className="space-y-4 max-h-[400px] overflow-y-auto pr-1">
            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Organization Name
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  required
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full bg-slate-900/40 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="Acme Corp"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Corporate Domain Scope
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  required
                  value={orgDomain}
                  onChange={(e) => setOrgDomain(e.target.value)}
                  className="w-full bg-slate-900/40 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="acme.com"
                />
              </div>
            </div>

            <div className="border-t border-slate-800/40 my-4 pt-4">
              <span className="block text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-3">
                Root Admin Account
              </span>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Admin Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  required
                  value={adminName}
                  onChange={(e) => setAdminName(e.target.value)}
                  className="w-full bg-slate-900/40 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Admin Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  className="w-full bg-slate-900/40 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="admin@acme.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                Admin Initial Password
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                <input
                  type="password"
                  required
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  className="w-full bg-slate-900/40 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-550 hover:bg-indigo-500 disabled:bg-indigo-850 text-white font-semibold text-xs tracking-wider py-3 rounded-xl transition-all cursor-pointer shadow-lg shadow-indigo-950/45 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <span className="w-4 h-4 rounded-full border-2 border-slate-300 border-t-transparent animate-spin"></span>
              ) : (
                <>
                  <Building2 className="w-4 h-4" />
                  <span>Onboard Organization Workspace</span>
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
export default Login;
