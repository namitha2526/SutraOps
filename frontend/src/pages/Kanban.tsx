import React, { useEffect, useState } from "react";
import { useStore } from "../store/useStore";
import { 
  CheckSquare, 
  ArrowRight, 
  UserCheck, 
  Check, 
  X,
  MessageSquare,
  AlertCircle
} from "lucide-react";

export const Kanban: React.FC = () => {
  const { 
    tasks, 
    fetchTasks, 
    updateTaskStatus,
    pendingApprovals,
    fetchApprovals,
    actionStepApproval,
    user
  } = useStore();

  const [decisionComments, setDecisionComments] = useState<{ [key: string]: string }>({});
  const [actingApprovalId, setActingApprovalId] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks();
    fetchApprovals();
  }, [fetchTasks, fetchApprovals]);

  // Kanban column definitions
  const columns = [
    { id: "Todo", title: "To Do", bg: "bg-slate-900/40", border: "border-slate-800/40" },
    { id: "InProgress", title: "In Progress", bg: "bg-indigo-500/5", border: "border-indigo-500/10" },
    { id: "InReview", title: "In Review", bg: "bg-amber-500/5", border: "border-amber-500/10" },
    { id: "Done", title: "Completed", bg: "bg-emerald-500/5", border: "border-emerald-500/10" }
  ];

  const handleDecision = async (approvalId: string, status: "Approved" | "Rejected") => {
    setActingApprovalId(approvalId);
    const comments = decisionComments[approvalId] || "";

    try {
      await actionStepApproval(approvalId, status, comments);
      alert(`Step ${status} committed successfully.`);
      // Clear comments input
      setDecisionComments({ ...decisionComments, [approvalId]: "" });
      fetchTasks();  // Reload tasks since state updated
    } catch (err: any) {
      alert("Signoff failed: " + (err.response?.data?.message || "Unauthorized"));
    } finally {
      setActingApprovalId(null);
    }
  };

  return (
    <div className="flex-1 p-8 space-y-8 select-none relative overflow-y-auto min-h-screen">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Board & Tasks Workspace</h1>
        <p className="text-slate-400 text-sm mt-1">Review items requiring your sign-off and manage team progress boards.</p>
      </div>

      {/* PENDING APPROVALS SIGN-OFF BAR */}
      {pendingApprovals.length > 0 && (
        <div className="glass-panel border-indigo-500/30 p-6 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center space-x-2.5">
            <UserCheck className="w-5 h-5 text-indigo-400" />
            <span className="text-sm font-bold text-slate-200">Pending Approvals Assigned To Your Role</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-indigo-500/20 text-indigo-400 font-bold uppercase tracking-wider">
              Requires Signature
            </span>
          </div>

          <div className="grid grid-cols-2 gap-6">
            {pendingApprovals.map((app) => (
              <div 
                key={app.id} 
                className="p-5 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors"
              >
                <div className="space-y-1.5">
                  <span className="block text-[10px] text-indigo-400 font-bold uppercase tracking-wider">
                    Step: {app.step?.name}
                  </span>
                  <span className="block text-xs font-bold text-slate-200">
                    {app.workflow?.title}
                  </span>
                  <p className="text-[11px] text-slate-400 leading-relaxed truncate">
                    {app.workflow?.description}
                  </p>
                </div>

                {/* Remarks comment input */}
                <div className="space-y-2">
                  <div className="relative">
                    <MessageSquare className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-500" />
                    <input
                      type="text"
                      value={decisionComments[app.id] || ""}
                      onChange={(e) => setDecisionComments({ ...decisionComments, [app.id]: e.target.value })}
                      className="w-full bg-slate-900/60 border border-slate-850 rounded-xl pl-9 pr-4 py-2 text-[10px] text-slate-200 focus:outline-none focus:border-indigo-500"
                      placeholder="Add sign-off audit remarks..."
                    />
                  </div>

                  <div className="flex space-x-2">
                    <button
                      disabled={actingApprovalId === app.id}
                      onClick={() => handleDecision(app.id, "Approved")}
                      className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-900 text-white text-[10px] font-bold py-2 rounded-lg cursor-pointer flex items-center justify-center space-x-1.5 transition-colors"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Sign Approve</span>
                    </button>
                    <button
                      disabled={actingApprovalId === app.id}
                      onClick={() => handleDecision(app.id, "Rejected")}
                      className="flex-1 bg-rose-600 hover:bg-rose-500 disabled:bg-rose-900 text-white text-[10px] font-bold py-2 rounded-lg cursor-pointer flex items-center justify-center space-x-1.5 transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* KANBAN BOARD */}
      <div className="grid grid-cols-4 gap-6 items-start">
        {columns.map((col) => {
          const colTasks = tasks.filter((t) => t.status === col.id);
          return (
            <div key={col.id} className={`rounded-2xl border ${col.border} ${col.bg} p-4 space-y-4`}>
              <div className="flex justify-between items-center px-1">
                <span className="text-xs font-bold text-slate-200 tracking-wide">{col.title}</span>
                <span className="px-2 py-0.5 rounded-full text-[9px] bg-slate-800/80 text-slate-400 font-semibold">
                  {colTasks.length}
                </span>
              </div>

              <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                {colTasks.length === 0 ? (
                  <div className="p-8 text-center text-slate-600 text-[10px]">
                    No items in this lane.
                  </div>
                ) : (
                  colTasks.map((task) => (
                    <div 
                      key={task.id}
                      className="p-4 rounded-xl bg-slate-950/60 border border-slate-850 hover:border-slate-700/80 transition-all duration-200 space-y-3 group"
                    >
                      <div className="space-y-1">
                        <span className="block text-xs font-bold text-slate-200 leading-snug group-hover:text-white transition-colors">
                          {task.title}
                        </span>
                        <span className="block text-[10px] text-slate-400 leading-normal">
                          {task.description}
                        </span>
                      </div>

                      <div className="flex justify-between items-center border-t border-slate-900/60 pt-2.5">
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider ${
                          task.priority === "High" || task.priority === "Urgent"
                            ? "bg-rose-500/10 text-rose-400"
                            : "bg-indigo-500/10 text-indigo-400"
                        }`}>
                          {task.priority} Priority
                        </span>

                        {col.id !== "Done" && (
                          <button
                            onClick={() => {
                              const nextStatus = 
                                col.id === "Todo" ? "InProgress" : 
                                col.id === "InProgress" ? "InReview" : "Done";
                              updateTaskStatus(task.id, nextStatus);
                            }}
                            className="p-1 rounded bg-slate-900 hover:bg-indigo-600 hover:text-white text-slate-400 transition-all cursor-pointer"
                            title="Move to next status"
                          >
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
export default Kanban;
