import React, { useEffect, useState } from "react";
import { useStore } from "../store/useStore";
import { api } from "../services/api";
import { 
  Users, 
  Building2, 
  Settings2, 
  Plus, 
  Mail, 
  ShieldAlert, 
  UserPlus, 
  Check, 
  ToggleLeft,
  ToggleRight,
  ShieldCheck
} from "lucide-react";

export const Admin: React.FC = () => {
  const { user } = useStore();
  const [activeSubTab, setActiveSubTab] = useState<"users" | "depts" | "flags">("users");
  const [users, setUsers] = useState<any[]>([]);
  const [depts, setDepts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // New User Form State
  const [showUserModal, setShowUserModal] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  const [userFullName, setUserFullName] = useState("");
  const [userRole, setUserRole] = useState("Employee");
  const [userDeptId, setUserDeptId] = useState("");
  const [userPassword, setUserPassword] = useState("");

  // New Dept Form State
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [deptName, setDeptName] = useState("");
  const [deptCode, setDeptCode] = useState("");

  // Feature Flags State
  const [flags, setFlags] = useState({
    enable_notifications: true,
    enable_escalation: true,
    enable_analytics: true
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [usersRes, deptsRes] = await Promise.all([
        api.get("/admin/users"),
        api.get("/admin/departments")
      ]);
      setUsers(usersRes.data);
      setDepts(deptsRes.data);
    } catch (e) {
      console.error("Failed fetching admin directories", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchFeatureFlags = async () => {
    try {
      // Fetch current state from health endpoint
      const res = await api.get("/health");
      const healthFlags = res.data.feature_flags;
      setFlags({
        enable_notifications: healthFlags.notifications_enabled,
        enable_escalation: healthFlags.escalations_enabled,
        enable_analytics: healthFlags.analytics_enabled
      });
    } catch (e) {}
  };

  useEffect(() => {
    fetchData();
    fetchFeatureFlags();
  }, []);

  const handleOnboardUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      const payload = {
        email: userEmail,
        full_name: userFullName,
        role: userRole,
        department_id: userDeptId || null,
        password: userPassword
      };
      await api.post("/admin/users", payload);
      alert(`User profile "${userFullName}" onboarded successfully.`);
      setShowUserModal(false);
      
      // Reset
      setUserEmail("");
      setUserFullName("");
      setUserRole("Employee");
      setUserDeptId("");
      setUserPassword("");

      fetchData();
    } catch (err: any) {
      alert("Failed to onboard user: " + (err.response?.data?.message || "Check inputs"));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateDept = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await api.post("/admin/departments", {
        name: deptName,
        code: deptCode
      });
      alert(`Department code "${deptCode}" provisioned.`);
      setShowDeptModal(false);
      
      // Reset
      setDeptName("");
      setDeptCode("");

      fetchData();
    } catch (err: any) {
      alert("Failed creating department: " + (err.response?.data?.message || "Check fields"));
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleFlag = async (key: keyof typeof flags, currentVal: boolean) => {
    const nextFlags = { ...flags, [key]: !currentVal };
    try {
      const res = await api.post(
        `/admin/feature-flags?enable_notifications=${nextFlags.enable_notifications}&enable_escalation=${nextFlags.enable_escalation}&enable_analytics=${nextFlags.enable_analytics}`
      );
      setFlags({
        enable_notifications: res.data.current_state.enable_notifications,
        enable_escalation: res.data.current_state.enable_escalation,
        enable_analytics: res.data.current_state.enable_analytics
      });
    } catch (e) {
      alert("Failed to toggle feature flag");
    }
  };

  // Auth access checks
  const isAuthorized = user?.role === "Admin" || user?.role === "SuperAdmin";

  if (!isAuthorized) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center space-y-4 min-h-screen bg-slate-950 p-6">
        <div className="p-4 bg-rose-500/10 rounded-2xl border border-rose-500/20 text-rose-400">
          <ShieldAlert className="w-12 h-12" />
        </div>
        <h2 className="text-lg font-bold text-white tracking-wide">Unauthorized Console Scope</h2>
        <p className="text-slate-400 text-xs text-center max-w-sm leading-relaxed">
          Access to Tenant Administration properties requires system-validated Admin or SuperAdmin clearance tokens.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 space-y-8 select-none relative overflow-y-auto min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Tenant Control Console</h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage corporate department codes, onboard personnel accounts, and override operational feature toggles.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 bg-slate-900/40 p-1.5 rounded-2xl border border-slate-800/60 w-max">
        <button
          onClick={() => setActiveSubTab("users")}
          className={`px-5 py-2.5 rounded-xl text-xs font-semibold tracking-wide cursor-pointer transition-all flex items-center space-x-2 ${
            activeSubTab === "users"
              ? "bg-indigo-550 text-white shadow-md"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Team Directory</span>
        </button>

        <button
          onClick={() => setActiveSubTab("depts")}
          className={`px-5 py-2.5 rounded-xl text-xs font-semibold tracking-wide cursor-pointer transition-all flex items-center space-x-2 ${
            activeSubTab === "depts"
              ? "bg-indigo-550 text-white shadow-md"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>Departments Registry</span>
        </button>

        <button
          onClick={() => setActiveSubTab("flags")}
          className={`px-5 py-2.5 rounded-xl text-xs font-semibold tracking-wide cursor-pointer transition-all flex items-center space-x-2 ${
            activeSubTab === "flags"
              ? "bg-indigo-550 text-white shadow-md"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Settings2 className="w-4 h-4" />
          <span>Feature Control Room</span>
        </button>
      </div>

      {/* Main Contents Panel */}
      <div className="glass-panel rounded-3xl p-6 shadow-2xl relative overflow-hidden">
        {loading ? (
          <div className="p-20 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-2">
            <span className="w-6 h-6 rounded-full border-2 border-slate-700 border-t-indigo-400 animate-spin"></span>
            <span>Fetching organization directories...</span>
          </div>
        ) : (
          <>
            {/* SUBTAB 1: TEAM DIRECTORY */}
            {activeSubTab === "users" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center pb-2">
                  <div>
                    <h3 className="text-sm font-bold text-slate-200">Corporate Team Directory</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">Registers accounts mapping to specific workflow roles.</p>
                  </div>
                  <button
                    onClick={() => setShowUserModal(true)}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 cursor-pointer transition-all"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Onboard Personnel</span>
                  </button>
                </div>

                <div className="overflow-hidden rounded-2xl border border-slate-900">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-900/50 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-900">
                        <th className="p-4">Personnel Profile</th>
                        <th className="p-4">Email Username</th>
                        <th className="p-4">Role Matrix</th>
                        <th className="p-4">Assigned Department</th>
                        <th className="p-4 text-right">System Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-900/60 text-xs text-slate-350">
                      {users.map((u) => (
                        <tr key={u.id} className="hover:bg-slate-900/15">
                          <td className="p-4 font-semibold text-slate-200 flex items-center space-x-3">
                            <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-750 flex items-center justify-center font-bold text-slate-300 text-[10px]">
                              {u.full_name.charAt(0)}
                            </div>
                            <span>{u.full_name}</span>
                          </td>
                          <td className="p-4 font-mono text-slate-400">{u.email}</td>
                          <td className="p-4">
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                              u.role === "Admin" || u.role === "SuperAdmin"
                                ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                                : u.role === "Manager"
                                ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                                : "bg-slate-800 text-slate-400"
                            }`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="p-4">
                            <span className="font-semibold text-slate-250">
                              {u.department ? `${u.department.name} (${u.department.code})` : "General Scope"}
                            </span>
                          </td>
                          <td className="p-4 text-right">
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                              u.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-800 text-slate-500"
                            }`}>
                              {u.is_active ? "Active" : "Suspended"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* SUBTAB 2: DEPARTMENTS REGISTRY */}
            {activeSubTab === "depts" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center pb-2">
                  <div>
                    <h3 className="text-sm font-bold text-slate-200">Department Registers</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">Provision functional units governing step logic paths.</p>
                  </div>
                  <button
                    onClick={() => setShowDeptModal(true)}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center space-x-2 cursor-pointer transition-all"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create Department</span>
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-6">
                  {depts.map((d) => (
                    <div 
                      key={d.id}
                      className="p-5 rounded-2xl bg-slate-900/20 border border-slate-850 hover:border-slate-800 transition-colors flex items-center justify-between"
                    >
                      <div className="space-y-1">
                        <span className="block text-xs font-bold text-slate-200">{d.name}</span>
                        <span className="block text-[9px] font-bold text-indigo-400 uppercase tracking-widest">{d.code} Department</span>
                      </div>
                      <div className="p-2 bg-indigo-500/5 rounded-xl border border-indigo-500/10 text-indigo-450">
                        <Building2 className="w-4 h-4" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* SUBTAB 3: FEATURE FLAGS */}
            {activeSubTab === "flags" && (
              <div className="space-y-6">
                <div className="pb-2">
                  <h3 className="text-sm font-bold text-slate-200">System Capabilities Toggles</h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">Dynamically activate and bypass global process filters.</p>
                </div>

                <div className="space-y-4 max-w-xl">
                  {/* Flag 1 */}
                  <div className="p-5 rounded-2xl bg-slate-900/20 border border-slate-850 flex items-center justify-between">
                    <div className="space-y-1 max-w-[75%]">
                      <span className="block text-xs font-bold text-slate-200">SLA Step Escalation Monitor</span>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        When enabled, processes breaching their configured SLA deadlines are automatically flagged and escalated.
                      </p>
                    </div>
                    <button
                      onClick={() => handleToggleFlag("enable_escalation", flags.enable_escalation)}
                      className="text-indigo-450 hover:text-indigo-400 cursor-pointer transition-all"
                    >
                      {flags.enable_escalation ? (
                        <ToggleRight className="w-12 h-12 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-12 h-12 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Flag 2 */}
                  <div className="p-5 rounded-2xl bg-slate-900/20 border border-slate-850 flex items-center justify-between">
                    <div className="space-y-1 max-w-[75%]">
                      <span className="block text-xs font-bold text-slate-200">Real-time Email Alerts & Alerts Feed</span>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        Dispatches in-app notifications and email summaries when step approvals are assigned to role contexts.
                      </p>
                    </div>
                    <button
                      onClick={() => handleToggleFlag("enable_notifications", flags.enable_notifications)}
                      className="text-indigo-450 hover:text-indigo-400 cursor-pointer transition-all"
                    >
                      {flags.enable_notifications ? (
                        <ToggleRight className="w-12 h-12 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-12 h-12 text-slate-600" />
                      )}
                    </button>
                  </div>

                  {/* Flag 3 */}
                  <div className="p-5 rounded-2xl bg-slate-900/20 border border-slate-850 flex items-center justify-between">
                    <div className="space-y-1 max-w-[75%]">
                      <span className="block text-xs font-bold text-slate-200">Performance Telemetry Hub</span>
                      <p className="text-[11px] text-slate-400 leading-relaxed">
                        Enables analytical calculators evaluating department throughput indexes and composite efficiency scores.
                      </p>
                    </div>
                    <button
                      onClick={() => handleToggleFlag("enable_analytics", flags.enable_analytics)}
                      className="text-indigo-450 hover:text-indigo-400 cursor-pointer transition-all"
                    >
                      {flags.enable_analytics ? (
                        <ToggleRight className="w-12 h-12 text-indigo-500" />
                      ) : (
                        <ToggleLeft className="w-12 h-12 text-slate-600" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* USER ONBOARD MODAL */}
      {showUserModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md glass-panel border border-slate-800 rounded-3xl p-8 space-y-6 shadow-2xl glass-panel-glow">
            <div className="flex justify-between items-center border-b border-slate-800/60 pb-4">
              <h3 className="text-md font-bold text-white tracking-wide">Onboard Personnel Profile</h3>
              <button
                onClick={() => setShowUserModal(false)}
                className="text-slate-400 hover:text-white text-xs cursor-pointer"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleOnboardUser} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={userFullName}
                  onChange={(e) => setUserFullName(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. John Doe"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Corporate Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={userEmail}
                    onChange={(e) => setUserEmail(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                    placeholder="name@sutraops.com"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Role Context
                  </label>
                  <select
                    value={userRole}
                    onChange={(e) => setUserRole(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none"
                  >
                    <option value="Employee">Employee</option>
                    <option value="Manager">Manager</option>
                    <option value="Admin">Admin</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Department
                  </label>
                  <select
                    value={userDeptId}
                    onChange={(e) => setUserDeptId(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none"
                  >
                    <option value="">-- General / No Dept --</option>
                    {depts.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Initial Password
                </label>
                <input
                  type="password"
                  required
                  value={userPassword}
                  onChange={(e) => setUserPassword(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                className="w-full bg-indigo-650 hover:bg-indigo-600 disabled:bg-indigo-900 text-white font-semibold text-xs tracking-wider py-3 rounded-xl shadow-lg cursor-pointer transition-all flex items-center justify-center space-x-2"
              >
                {actionLoading ? (
                  <span className="w-4 h-4 rounded-full border-2 border-slate-350 border-t-transparent animate-spin"></span>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Authorize Onboarding</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* DEPT PROVISION MODAL */}
      {showDeptModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md glass-panel border border-slate-800 rounded-3xl p-8 space-y-6 shadow-2xl glass-panel-glow">
            <div className="flex justify-between items-center border-b border-slate-800/60 pb-4">
              <h3 className="text-md font-bold text-white tracking-wide">Provision Department Unit</h3>
              <button
                onClick={() => setShowDeptModal(false)}
                className="text-slate-400 hover:text-white text-xs cursor-pointer"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleCreateDept} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Department Name
                </label>
                <input
                  type="text"
                  required
                  value={deptName}
                  onChange={(e) => setDeptName(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. Marketing & Communication"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Unique Department Code
                </label>
                <input
                  type="text"
                  required
                  value={deptCode}
                  onChange={(e) => setDeptCode(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. MKT"
                />
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                className="w-full bg-indigo-650 hover:bg-indigo-600 disabled:bg-indigo-900 text-white font-semibold text-xs tracking-wider py-3 rounded-xl shadow-lg cursor-pointer transition-all flex items-center justify-center space-x-2"
              >
                {actionLoading ? (
                  <span className="w-4 h-4 rounded-full border-2 border-slate-350 border-t-transparent animate-spin"></span>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Deploy Department Unit</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default Admin;
