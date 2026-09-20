import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { 
  AlertOctagon, 
  Clock, 
  BarChart3, 
  Activity,
  Layers,
  Award,
  Zap,
  Building
} from "lucide-react";

export const Analytics: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTelemetry = async () => {
    try {
      setLoading(true);
      const res = await api.get("/analytics");
      setData(res.data);
    } catch (e) {
      console.error("Failed fetching performance telemetry", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center space-y-4 min-h-screen bg-slate-950">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-slate-800"></div>
          <div className="absolute inset-0 rounded-full border-4 border-t-indigo-500 border-r-indigo-500 animate-spin"></div>
        </div>
        <p className="text-slate-400 text-sm font-medium tracking-wide animate-pulse">
          Calculating SLA breaches and corporate metrics telemetry...
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex-1 p-8 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-3 min-h-screen">
        <AlertOctagon className="w-8 h-8 text-slate-700 animate-pulse-subtle" />
        <span>Failed loading analytics dashboard. Verify server connectivity.</span>
      </div>
    );
  }

  const { summary, performance, department_metrics } = data;
  const totalWfs = summary.total_workflows || 0;

  // Calculate percentages for the stacked status progress bar
  const approvedPct = totalWfs > 0 ? (summary.approved / totalWfs) * 100 : 0;
  const pendingPct = totalWfs > 0 ? ((summary.pending + summary.escalated) / totalWfs) * 100 : 0;
  const rejectedPct = totalWfs > 0 ? (summary.rejected / totalWfs) * 100 : 0;
  const draftPct = totalWfs > 0 ? (summary.draft / totalWfs) * 100 : 0;

  return (
    <div className="flex-1 p-8 space-y-8 select-none relative overflow-y-auto min-h-screen">
      {/* Upper header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">SLA Performance Telemetry</h1>
          <p className="text-slate-400 text-sm mt-1">
            Compute average approval latencies, track SLA breaches, and evaluate workflow efficiency index.
          </p>
        </div>

        <button
          onClick={fetchTelemetry}
          className="bg-slate-900 hover:bg-slate-850 text-slate-200 border border-slate-800 text-xs font-semibold px-4 py-2.5 rounded-xl cursor-pointer flex items-center space-x-2 transition-all"
        >
          <Activity className="w-4 h-4 text-indigo-400" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* CORE KPI METRICS */}
      <div className="grid grid-cols-4 gap-6">
        {/* KPI 1: Efficiency Score */}
        <div className="glass-panel border-indigo-500/20 p-6 rounded-2xl flex items-center justify-between shadow-lg relative overflow-hidden group">
          <div className="space-y-2.5 z-10">
            <span className="block text-[10px] text-slate-400 uppercase tracking-widest font-bold">Workflow Efficiency</span>
            <span className="block text-3xl font-extrabold text-white mt-1">{performance.workflow_efficiency_score}%</span>
            <span className="block text-[10px] text-indigo-400 font-semibold flex items-center space-x-1">
              <Award className="w-3.5 h-3.5" />
              <span>Target Standard: &gt; 80%</span>
            </span>
          </div>
          <div className="relative w-16 h-16 flex items-center justify-center z-10">
            {/* Visual Circular CSS Gauge */}
            <svg className="w-16 h-16 transform -rotate-90">
              <circle
                cx="32"
                cy="32"
                r="26"
                stroke="rgba(30, 41, 59, 0.5)"
                strokeWidth="5"
                fill="transparent"
              />
              <circle
                cx="32"
                cy="32"
                r="26"
                stroke="url(#indigoGrad)"
                strokeWidth="5"
                fill="transparent"
                strokeDasharray="163"
                strokeDashoffset={163 - (163 * Math.min(100, Math.max(0, performance.workflow_efficiency_score))) / 100}
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="indigoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#818cf8" />
                  <stop offset="100%" stopColor="#4f46e5" />
                </linearGradient>
              </defs>
            </svg>
            <span className="absolute text-[10px] font-bold text-slate-350">{Math.round(performance.workflow_efficiency_score)}%</span>
          </div>
        </div>

        {/* KPI 2: SLA Breaches */}
        <div className={`glass-panel p-6 rounded-2xl flex items-center space-x-4 shadow-lg transition-all ${
          performance.sla_breach_count > 0 ? "border-rose-500/30 bg-rose-950/5" : "border-slate-800/40"
        }`}>
          <div className={`p-3 rounded-xl border ${
            performance.sla_breach_count > 0 
              ? "bg-rose-500/10 border-rose-500/20 text-rose-400" 
              : "bg-slate-900/60 border-slate-800 text-slate-400"
          }`}>
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <span className="block text-[10px] text-slate-400 uppercase tracking-widest font-bold">Active SLA Breaches</span>
            <span className="block text-3xl font-extrabold text-white mt-1">{performance.sla_breach_count}</span>
            <span className={`block text-[10px] font-semibold ${
              performance.sla_breach_count > 0 ? "text-rose-400 animate-pulse" : "text-emerald-400"
            }`}>
              {performance.sla_breach_count > 0 ? "Immediate Action Required" : "All approvals on schedule"}
            </span>
          </div>
        </div>

        {/* KPI 3: Avg Latency */}
        <div className="glass-panel border-slate-800/40 p-6 rounded-2xl flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-indigo-400">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="block text-[10px] text-slate-400 uppercase tracking-widest font-bold">Average Approval Time</span>
            <span className="block text-3xl font-extrabold text-white mt-1">{performance.average_latency_hours}h</span>
            <span className="block text-[10px] text-slate-500">
              Average timeline per signoff
            </span>
          </div>
        </div>

        {/* KPI 4: Escalation Rate */}
        <div className="glass-panel border-slate-800/40 p-6 rounded-2xl flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-amber-500/10 rounded-xl border border-amber-500/20 text-amber-400">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <span className="block text-[10px] text-slate-400 uppercase tracking-widest font-bold">Escalation Rate</span>
            <span className="block text-3xl font-extrabold text-white mt-1">{performance.escalation_frequency_percentage}%</span>
            <span className="block text-[10px] text-slate-500">
              {summary.escalated} of {totalWfs} workflows escalated
            </span>
          </div>
        </div>
      </div>

      {/* CORE WORKFLOW telemetry breakdown */}
      <div className="grid grid-cols-3 gap-8">
        {/* Left main: Volume & Status Distribution */}
        <div className="col-span-2 space-y-6">
          <div className="glass-panel rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex justify-between items-center">
              <span className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                <span>Workflow Pipelines Status Mix</span>
              </span>
              <span className="text-xs font-semibold text-slate-400">Total volume: {totalWfs} runs</span>
            </div>

            {/* Custom pure CSS visual stacked progress chart bar */}
            <div className="space-y-4">
              <div className="w-full h-4 bg-slate-900 rounded-full overflow-hidden flex">
                <div 
                  style={{ width: `${approvedPct}%` }} 
                  className="bg-emerald-500 h-full transition-all duration-500" 
                  title={`Approved: ${summary.approved} (${Math.round(approvedPct)}%)`}
                ></div>
                <div 
                  style={{ width: `${pendingPct}%` }} 
                  className="bg-indigo-500 h-full transition-all duration-500" 
                  title={`Pending/Escalated: ${summary.pending + summary.escalated} (${Math.round(pendingPct)}%)`}
                ></div>
                <div 
                  style={{ width: `${rejectedPct}%` }} 
                  className="bg-rose-500 h-full transition-all duration-500" 
                  title={`Rejected: ${summary.rejected} (${Math.round(rejectedPct)}%)`}
                ></div>
                <div 
                  style={{ width: `${draftPct}%` }} 
                  className="bg-slate-700 h-full transition-all duration-500" 
                  title={`Draft: ${summary.draft} (${Math.round(draftPct)}%)`}
                ></div>
              </div>

              {/* Legend with individual counts */}
              <div className="grid grid-cols-4 gap-4 pt-2">
                <div className="p-3 bg-slate-900/30 border border-slate-900/80 rounded-xl space-y-1">
                  <div className="flex items-center space-x-1.5 text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>Approved</span>
                  </div>
                  <span className="block text-lg font-extrabold text-slate-200">{summary.approved}</span>
                </div>

                <div className="p-3 bg-slate-900/30 border border-slate-900/80 rounded-xl space-y-1">
                  <div className="flex items-center space-x-1.5 text-[10px] text-indigo-400 font-bold uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                    <span>Active Pending</span>
                  </div>
                  <span className="block text-lg font-extrabold text-slate-200">{summary.pending + summary.escalated}</span>
                </div>

                <div className="p-3 bg-slate-900/30 border border-slate-900/80 rounded-xl space-y-1">
                  <div className="flex items-center space-x-1.5 text-[10px] text-rose-400 font-bold uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                    <span>Rejected</span>
                  </div>
                  <span className="block text-lg font-extrabold text-slate-200">{summary.rejected}</span>
                </div>

                <div className="p-3 bg-slate-900/30 border border-slate-900/80 rounded-xl space-y-1">
                  <div className="flex items-center space-x-1.5 text-[10px] text-slate-450 font-bold uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-slate-700"></span>
                    <span>Draft State</span>
                  </div>
                  <span className="block text-lg font-extrabold text-slate-200">{summary.draft}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Department Breakdown table */}
          <div className="glass-panel rounded-2xl p-6 shadow-xl space-y-4">
            <span className="text-sm font-bold text-slate-200 flex items-center space-x-2 mb-2">
              <Building className="w-4 h-4 text-indigo-400" />
              <span>Department through-put volume & efficiency score</span>
            </span>

            <div className="overflow-hidden rounded-xl border border-slate-900">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-900/50 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-900">
                    <th className="p-4">Department Unit</th>
                    <th className="p-4">Process Volume Count</th>
                    <th className="p-4">Efficiency Performance</th>
                    <th className="p-4 text-right">Status Check</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900/60 text-xs">
                  {department_metrics.map((dept: any, idx: number) => {
                    const progressWidth = Math.min(100, Math.max(0, dept.efficiency));
                    return (
                      <tr key={idx} className="hover:bg-slate-900/15 transition-colors">
                        <td className="p-4 font-semibold text-slate-200">{dept.department}</td>
                        <td className="p-4 font-semibold text-slate-350">{dept.volume} runs</td>
                        <td className="p-4">
                          <div className="flex items-center space-x-3">
                            <span className="font-semibold text-slate-200 w-8">{Math.round(dept.efficiency)}%</span>
                            <div className="w-32 h-1.5 bg-slate-900 rounded-full overflow-hidden">
                              <div 
                                style={{ width: `${progressWidth}%` }} 
                                className="bg-indigo-500 h-full rounded-full"
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td className="p-4 text-right">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                            dept.efficiency >= 80 
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                              : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}>
                            {dept.efficiency >= 80 ? "Optimal" : "Escalation Watch"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right side: Performance recommendations */}
        <div className="col-span-1">
          <div className="glass-panel rounded-2xl p-6 shadow-xl space-y-6 sticky top-6">
            <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2 border-b border-slate-800/60 pb-3">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>SLA Audit Insights</span>
            </h3>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
                <span className="block text-[10px] text-indigo-400 font-bold uppercase tracking-wider">
                  Bottleneck Indicator
                </span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Average sign-off latency is currently <strong className="text-slate-200">{performance.average_latency_hours} hours</strong>. 
                  Identify stages with heavy human reviews and enable automated step skip criteria.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
                <span className="block text-[10px] text-indigo-400 font-bold uppercase tracking-wider">
                  Escalation Prevention
                </span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  The escalation frequency is currently <strong className="text-slate-200">{performance.escalation_frequency_percentage}%</strong>. 
                  Re-evaluate SLA timers in templates configuration to avoid automated breaches during holidays.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 space-y-2">
                <span className="block text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
                  System Recommendations
                </span>
                <ul className="text-[10px] text-slate-400 list-disc list-inside space-y-1 pt-1">
                  <li>Onboard 1 additional manager to IT department</li>
                  <li>Reduce approval SLA deadlines for Finance to 48 hours</li>
                  <li>Enable custom slack integration for real-time notifications</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Analytics;
