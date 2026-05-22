import React, { useEffect, useState } from "react";
import { useStore } from "../store/useStore";
import { api } from "../services/api";
import { 
  Play, 
  Plus, 
  Workflow as WorkflowIcon, 
  CheckCircle, 
  Clock, 
  XCircle, 
  FileText, 
  Send, 
  Paperclip,
  Check, 
  Info,
  Calendar,
  AlertTriangle
} from "lucide-react";

export const Dashboard: React.FC = () => {
  const { 
    workflows, 
    fetchWorkflows, 
    user 
  } = useStore();

  const [selectedWorkflow, setSelectedWorkflow] = useState<any | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Create workflow form states
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [workflowTitle, setWorkflowTitle] = useState("");
  const [workflowDesc, setWorkflowDesc] = useState("");
  const [amountField, setAmountField] = useState("6500");
  const [deptCodeField, setDeptCodeField] = useState("FIN");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Comments and attachments side-panel states
  const [comments, setComments] = useState<any[]>([]);
  const [newComment, setNewComment] = useState("");
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);

  useEffect(() => {
    fetchWorkflows();
    
    // Fetch available templates
    api.get("/templates").then((res) => {
      setTemplates(res.data);
      if (res.data.length > 0) {
        setSelectedTemplateId(res.data[0].id);
      }
    }).catch(() => {});
  }, [fetchWorkflows]);

  // Load detailed workflow details
  const handleSelectWorkflow = async (wf: any) => {
    setSelectedWorkflow(wf);
    setComments([]);
    setFileToUpload(null);

    try {
      const res = await api.get(`/approvals/${wf.id}/comments`);
      setComments(res.data);
    } catch (e) {}
  };

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // 1. Create Draft workflow
      const wfRes = await api.post("/workflows", {
        template_id: selectedTemplateId || null,
        title: workflowTitle,
        description: workflowDesc,
        context_data: {
          amount: parseFloat(amountField) || 0,
          department_code: deptCodeField
        }
      });

      // 2. Start process automatically (triggering Rules engine!)
      await api.post(`/workflows/${wfRes.data.id}/start`, {
        amount: parseFloat(amountField) || 0,
        department_code: deptCodeField
      });

      // Refresh listings
      await fetchWorkflows();
      setShowCreateModal(false);
      
      // Reset forms
      setWorkflowTitle("");
      setWorkflowDesc("");
      setAmountField("6500");
    } catch (err: any) {
      alert("Failed creating workflow: " + (err.response?.data?.message || "Check fields"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !selectedWorkflow) return;

    try {
      const res = await api.post(`/approvals/${selectedWorkflow.id}/comments`, {
        content: newComment
      });
      setComments([...comments, res.data]);
      setNewComment("");
    } catch (e) {}
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !selectedWorkflow) return;
    const file = e.target.files[0];
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post(`/approvals/${selectedWorkflow.id}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      alert("Document uploaded successfully and committed to step files catalog!");
      // Reload comments to show upload remark if any, or reload details
    } catch (e) {
      alert("Failed uploading attachment");
    }
  };

  // Status counters calculation
  const approvedCount = workflows.filter((w) => w.status === "Approved").length;
  const pendingCount = workflows.filter((w) => w.status === "Pending" || w.status === "Escalated").length;
  const rejectedCount = workflows.filter((w) => w.status === "Rejected").length;

  return (
    <div className="flex-1 p-8 space-y-8 select-none relative overflow-y-auto min-h-screen">
      {/* Upper header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Dynamic Process Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Review active approval chains and evaluate custom routing rules.</p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-lg shadow-indigo-950/40 cursor-pointer flex items-center space-x-2 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Launch Process Flow</span>
        </button>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-3 gap-6">
        <div className="glass-panel border-emerald-500/20 p-6 rounded-2xl flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
            <CheckCircle className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <span className="block text-[10px] text-slate-400 uppercase tracking-widest font-bold">Approved Processes</span>
            <span className="block text-2xl font-extrabold text-white mt-1">{approvedCount}</span>
          </div>
        </div>

        <div className="glass-panel border-indigo-500/20 p-6 rounded-2xl flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
            <Clock className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <span className="block text-[10px] text-slate-400 uppercase tracking-widest font-bold">Pending Execution</span>
            <span className="block text-2xl font-extrabold text-white mt-1">{pendingCount}</span>
          </div>
        </div>

        <div className="glass-panel border-rose-500/20 p-6 rounded-2xl flex items-center space-x-4 shadow-lg">
          <div className="p-3 bg-rose-500/10 rounded-xl border border-rose-500/20">
            <XCircle className="w-6 h-6 text-rose-400" />
          </div>
          <div>
            <span className="block text-[10px] text-slate-400 uppercase tracking-widest font-bold">Rejected Items</span>
            <span className="block text-2xl font-extrabold text-white mt-1">{rejectedCount}</span>
          </div>
        </div>
      </div>

      {/* Core layout grid */}
      <div className="grid grid-cols-3 gap-8">
        {/* Left main: Active Workflows Lists */}
        <div className="col-span-2 space-y-4">
          <div className="glass-panel rounded-2xl p-6 shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <span className="text-sm font-bold text-slate-200">Active Organization Pipelines</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-400 font-medium">
                {workflows.length} entries
              </span>
            </div>

            <div className="space-y-3.5">
              {workflows.length === 0 ? (
                <div className="p-12 text-center text-slate-500 text-xs">
                  No workflows initiated. Create a new process to get started.
                </div>
              ) : (
                workflows.map((wf) => {
                  const isPending = wf.status === "Pending" || wf.status === "Escalated";
                  return (
                    <div
                      key={wf.id}
                      onClick={() => handleSelectWorkflow(wf)}
                      className={`p-5 rounded-xl border transition-all duration-200 cursor-pointer flex justify-between items-center ${
                        selectedWorkflow?.id === wf.id
                          ? "bg-slate-900/60 border-indigo-500/80 shadow-md"
                          : "bg-slate-900/20 border-slate-800/40 hover:bg-slate-900/45 hover:border-slate-800"
                      }`}
                    >
                      <div className="space-y-1.5 max-w-[70%]">
                        <span className="block text-xs font-bold text-slate-200 tracking-wide truncate">
                          {wf.title}
                        </span>
                        <span className="block text-[11px] text-slate-400 truncate">
                          {wf.description}
                        </span>
                        <div className="flex items-center space-x-3 text-[10px] text-slate-500 pt-1">
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-3 h-3" />
                            <span>{new Date(wf.created_at).toLocaleDateString()}</span>
                          </span>
                          <span>•</span>
                          <span>Initiated by: {wf.creator?.full_name || "Employee"}</span>
                        </div>
                      </div>

                      <div className="flex flex-col items-end space-y-2">
                        <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                          wf.status === "Approved"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : isPending
                            ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}>
                          {wf.status}
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right side: Dynamic Visual Steps Canvas side panel */}
        <div className="col-span-1">
          {selectedWorkflow ? (
            <div className="glass-panel rounded-2xl p-6 shadow-xl space-y-6 sticky top-6 max-h-[85vh] overflow-y-auto">
              <div className="border-b border-slate-800/60 pb-4">
                <span className="block text-[10px] text-indigo-400 uppercase tracking-widest font-bold mb-1">
                  Active Canvas
                </span>
                <h2 className="text-sm font-bold text-white tracking-wide truncate">
                  {selectedWorkflow.title}
                </h2>
                <p className="text-[11px] text-slate-400 leading-relaxed mt-1">
                  {selectedWorkflow.description}
                </p>
              </div>

              {/* Vertical steps canvas visualization */}
              <div className="space-y-4">
                <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Process Steps Timeline
                </span>
                
                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {selectedWorkflow.steps?.map((step: any, idx: number) => {
                    const isStepApproved = step.approvals?.some((a: any) => a.status === "Approved");
                    const isStepPending = step.id === selectedWorkflow.current_step_id;
                    const isSkipped = step.approvals?.some((a: any) => a.comments?.includes("Bypassed"));
                    
                    return (
                      <div key={step.id} className="relative">
                        {/* Bullet Circle */}
                        <div className={`absolute -left-6 top-1.5 w-4 h-4 rounded-full flex items-center justify-center ring-4 ring-slate-950 ${
                          isStepApproved 
                            ? "bg-emerald-500" 
                            : isStepPending
                            ? "bg-indigo-500"
                            : isSkipped
                            ? "bg-slate-600"
                            : "bg-slate-800"
                        }`}>
                          {isStepApproved ? (
                            <Check className="w-2.5 h-2.5 text-white" />
                          ) : (
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-950"></span>
                          )}
                        </div>

                        <div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs font-bold text-slate-200">{step.name}</span>
                            {isSkipped && (
                              <span className="px-1.5 py-0.5 rounded text-[8px] bg-slate-800 text-slate-400 font-bold uppercase tracking-wide">
                                Skipped
                              </span>
                            )}
                          </div>
                          <span className="block text-[10px] text-indigo-400 font-medium uppercase tracking-wider mt-0.5">
                            Approver: {step.approver_role}
                          </span>
                          
                          {/* Rules logs context summary details */}
                          {step.rule_definition && (
                            <div className="mt-1.5 p-2 rounded-lg bg-slate-900/60 border border-slate-800/40 flex items-start space-x-1.5 text-[9px] text-slate-400 leading-relaxed">
                              <Info className="w-3 h-3 text-indigo-400 mt-0.5 flex-shrink-0" />
                              <div>
                                <span className="font-bold text-slate-300 block">Dynamic Step Rule:</span>
                                {step.rule_definition.conditions?.map((c: any, i: number) => (
                                  <span key={i} className="block font-mono">
                                    IF {c.field} {c.operator} {c.value} THEN {step.rule_definition.action}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Collaborative Comments thread logs */}
              <div className="border-t border-slate-800/60 pt-4 space-y-4">
                <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Audit Remarks & Comments
                </span>

                <div className="max-h-40 overflow-y-auto space-y-2.5 pr-1">
                  {comments.length === 0 ? (
                    <div className="p-3 text-center text-slate-600 text-[10px]">
                      No remarks posted. Action logs will appear here.
                    </div>
                  ) : (
                    comments.map((c) => (
                      <div key={c.id} className="p-2.5 rounded-lg bg-slate-900/40 border border-slate-800/30 space-y-1">
                        <div className="flex justify-between text-[9px] text-indigo-400 font-semibold">
                          <span>{c.user?.full_name}</span>
                          <span className="text-slate-500 font-normal">
                            {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-300 leading-relaxed">{c.content}</p>
                      </div>
                    ))
                  )}
                </div>

                <form onSubmit={handleAddComment} className="flex items-center space-x-2">
                  <input
                    type="text"
                    required
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    className="flex-1 bg-slate-900/40 border border-slate-800 rounded-xl px-3 py-2 text-[11px] text-slate-200 focus:outline-none focus:border-indigo-500"
                    placeholder="Add audit comment remark..."
                  />
                  <button
                    type="submit"
                    className="p-2 bg-indigo-650 hover:bg-indigo-600 text-white rounded-xl cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

              {/* File Attachment Upload */}
              <div className="border-t border-slate-800/60 pt-4 space-y-3">
                <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Document Attachments
                </span>
                
                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-2 px-3 py-2 bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 rounded-xl text-[10px] font-semibold text-slate-300 cursor-pointer transition-colors">
                    <Paperclip className="w-3.5 h-3.5 text-slate-400" />
                    <span>Upload Document</span>
                    <input
                      type="file"
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                  </label>
                  <span className="text-[9px] text-slate-500">Supports PDF, XLSX up to 10MB</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel rounded-2xl p-12 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-3">
              <WorkflowIcon className="w-8 h-8 text-slate-700 animate-pulse-subtle" />
              <span>Select a pipeline workflow to load detailed execution steps, comments, and attachments canvas.</span>
            </div>
          )}
        </div>
      </div>

      {/* CREATE WORKFLOW MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-lg glass-panel border border-slate-800 rounded-3xl p-8 space-y-6 shadow-2xl glass-panel-glow">
            <div className="flex justify-between items-center border-b border-slate-800/60 pb-4">
              <h3 className="text-md font-bold text-white tracking-wide">Launch Process Flow</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white text-xs cursor-pointer"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleCreateWorkflow} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Select Workflow Template
                </label>
                <select
                  value={selectedTemplateId}
                  onChange={(e) => setSelectedTemplateId(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">-- Custom Manual Step Configuration --</option>
                  {templates.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.category})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Process Title / Purpose
                </label>
                <input
                  type="text"
                  required
                  value={workflowTitle}
                  onChange={(e) => setWorkflowTitle(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. Q3 Cloud Infrastructure Tools Upgrade"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Detailed Scope Remarks
                </label>
                <textarea
                  required
                  value={workflowDesc}
                  onChange={(e) => setWorkflowDesc(e.target.value)}
                  rows={3}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="Describe scope, reasons, and objectives..."
                />
              </div>

              <div className="border-t border-slate-800/40 pt-4">
                <span className="block text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-3">
                  Dynamic Rule Parameters Context
                </span>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      Transaction Amount ($)
                    </label>
                    <input
                      type="number"
                      required
                      value={amountField}
                      onChange={(e) => setAmountField(e.target.value)}
                      className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none"
                      placeholder="e.g. 15000"
                    />
                  </div>

                  <div>
                    <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      Initiating Department Code
                    </label>
                    <select
                      value={deptCodeField}
                      onChange={(e) => setDeptCodeField(e.target.value)}
                      className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none"
                    >
                      <option value="FIN">FIN (Finance)</option>
                      <option value="IT">IT (Info Tech)</option>
                      <option value="HR">HR (Human Resources)</option>
                      <option value="EXEC">EXEC (Executives)</option>
                    </select>
                  </div>
                </div>

                <div className="mt-4 p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex items-start space-x-2 text-[10px] text-slate-400 leading-relaxed">
                  <AlertTriangle className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <span>
                    NexusFlow will process these context fields against defined templates conditions in real-time to auto-approve, skip, or route steps.
                  </span>
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900 text-white font-semibold text-xs tracking-wider py-3 rounded-xl shadow-lg cursor-pointer transition-all flex items-center justify-center space-x-2"
              >
                {isSubmitting ? (
                  <span className="w-4 h-4 rounded-full border-2 border-slate-300 border-t-transparent animate-spin"></span>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    <span>Launch & Run Rules Engine</span>
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
export default Dashboard;
