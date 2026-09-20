import React, { useEffect, useState } from "react";
import { useStore } from "../store/useStore";
import { api } from "../services/api";
import { 
  Plus, 
  Search, 
  Layers, 
  Sparkles, 
  BookOpen, 
  ArrowRight,
  Info,
  Sliders
} from "lucide-react";

interface StepCondition {
  field: string;
  operator: string;
  value: string;
}

interface StepDefinition {
  name: string;
  step_order: number;
  approver_role: string;
  rule_definition: {
    conditions: StepCondition[];
    action: string;
    action_value?: string;
  } | null;
}

export const Templates: React.FC = () => {
  const { user } = useStore();
  const [templates, setTemplates] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedTemplate, setSelectedTemplate] = useState<any | null>(null);
  
  // Custom template modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [templateDesc, setTemplateDesc] = useState("");
  const [templateCategory, setTemplateCategory] = useState("Procurement");
  const [steps, setSteps] = useState<StepDefinition[]>([
    {
      name: "Initial Approval",
      step_order: 1,
      approver_role: "Manager",
      rule_definition: null
    }
  ]);

  const fetchTemplates = async () => {
    try {
      const res = await api.get("/templates");
      setTemplates(res.data);
      if (res.data.length > 0 && !selectedTemplate) {
        setSelectedTemplate(res.data[0]);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const categories = ["All", "Finance", "IT", "HR", "Compliance"];
  
  const filteredTemplates = templates.filter((t) => {
    const matchesSearch = t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          t.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || t.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleImportBlueprint = async (tmpl: any) => {
    try {
      await api.post("/templates/import-blueprint", {
        name: tmpl.name,
        description: tmpl.description,
        category: tmpl.category,
        structure: tmpl.structure
      });
      alert(`Blueprint "${tmpl.name}" successfully imported to your corporate active directory.`);
      fetchTemplates();
    } catch (err: any) {
      alert("Failed to import blueprint: " + (err.response?.data?.message || "Internal error"));
    }
  };

  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (steps.length === 0) {
      alert("Please add at least one step to the workflow blueprint");
      return;
    }

    try {
      const payload = {
        name: templateName,
        description: templateDesc,
        category: templateCategory,
        structure: {
          steps: steps.map((s, idx) => ({
            ...s,
            step_order: idx + 1
          }))
        }
      };

      await api.post("/templates", payload);
      alert(`Template "${templateName}" created successfully.`);
      setShowCreateModal(false);
      
      // Reset state
      setTemplateName("");
      setTemplateDesc("");
      setTemplateCategory("Procurement");
      setSteps([
        {
          name: "Initial Approval",
          step_order: 1,
          approver_role: "Manager",
          rule_definition: null
        }
      ]);
      
      fetchTemplates();
    } catch (err: any) {
      alert("Failed creating custom template: " + (err.response?.data?.message || "Check fields"));
    }
  };

  const handleAddStep = () => {
    setSteps([
      ...steps,
      {
        name: `Approval Step ${steps.length + 1}`,
        step_order: steps.length + 1,
        approver_role: "Manager",
        rule_definition: null
      }
    ]);
  };

  const handleRemoveStep = (index: number) => {
    const newSteps = steps.filter((_, i) => i !== index);
    setSteps(newSteps.map((s, idx) => ({ ...s, step_order: idx + 1 })));
  };

  const handleStepChange = (index: number, field: string, value: any) => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  };

  const handleToggleRule = (index: number, enabled: boolean) => {
    const newSteps = [...steps];
    if (enabled) {
      newSteps[index].rule_definition = {
        conditions: [{ field: "amount", operator: ">", value: "5000" }],
        action: "ROUTE_TO_ROLE",
        action_value: "Admin"
      };
    } else {
      newSteps[index].rule_definition = null;
    }
    setSteps(newSteps);
  };

  const handleRuleConditionChange = (stepIdx: number, condIdx: number, field: string, value: any) => {
    const newSteps = [...steps];
    const rule = newSteps[stepIdx].rule_definition;
    if (rule) {
      rule.conditions[condIdx] = { ...rule.conditions[condIdx], [field]: value };
      setSteps(newSteps);
    }
  };

  const handleRuleActionChange = (stepIdx: number, field: string, value: any) => {
    const newSteps = [...steps];
    const rule = newSteps[stepIdx].rule_definition;
    if (rule) {
      newSteps[stepIdx].rule_definition = { ...rule, [field]: value };
      setSteps(newSteps);
    }
  };

  const isAdmin = user?.role === "Admin" || user?.role === "SuperAdmin";

  return (
    <div className="flex-1 p-8 space-y-8 select-none relative overflow-y-auto min-h-screen">
      {/* Upper header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Marketplace & Workflow Blueprints</h1>
          <p className="text-slate-400 text-sm mt-1">
            Browse global process definitions, import standardized models, and deploy tenant-specific automation rules.
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-lg shadow-indigo-950/40 cursor-pointer flex items-center space-x-2 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Create Custom Template</span>
          </button>
        )}
      </div>

      {/* Categories & Search Panel */}
      <div className="flex justify-between items-center bg-slate-900/40 p-3 rounded-2xl border border-slate-800/60">
        <div className="flex space-x-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all cursor-pointer ${
                selectedCategory === cat
                  ? "bg-indigo-550 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-80">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search template blueprints..."
            className="w-full bg-slate-950/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Core split panel layout */}
      <div className="grid grid-cols-3 gap-8">
        {/* Left side: Blueprints List */}
        <div className="col-span-2 space-y-4">
          <div className="glass-panel rounded-2xl p-6 shadow-xl">
            <h3 className="text-sm font-bold text-slate-200 mb-6 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Available Process Blueprints</span>
            </h3>

            <div className="grid grid-cols-2 gap-4">
              {filteredTemplates.length === 0 ? (
                <div className="col-span-2 p-12 text-center text-slate-500 text-xs">
                  No templates match the active filters or search criteria.
                </div>
              ) : (
                filteredTemplates.map((tmpl) => {
                  const isMarketplace = tmpl.organization_id === null;
                  return (
                    <div
                      key={tmpl.id}
                      onClick={() => setSelectedTemplate(tmpl)}
                      className={`p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between space-y-4 hover:scale-[1.01] ${
                        selectedTemplate?.id === tmpl.id
                          ? "bg-slate-900/60 border-indigo-500/80 shadow-md shadow-indigo-950/20"
                          : "bg-slate-900/20 border-slate-800/40 hover:bg-slate-900/40 hover:border-slate-800"
                      }`}
                    >
                      <div className="space-y-2">
                        <div className="flex justify-between items-start">
                          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wider">
                            {tmpl.category}
                          </span>
                          {isMarketplace ? (
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-800 text-slate-400 border border-slate-700/30 uppercase tracking-wider flex items-center space-x-1">
                              <Sparkles className="w-3 h-3 text-amber-400" />
                              <span>Marketplace</span>
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
                              Tenant Custom
                            </span>
                          )}
                        </div>

                        <span className="block text-xs font-bold text-slate-200 tracking-wide pt-1">
                          {tmpl.name}
                        </span>
                        <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
                          {tmpl.description}
                        </p>
                      </div>

                      <div className="flex items-center justify-between border-t border-slate-800/60 pt-3 text-[10px] text-slate-500">
                        <span>Steps: {tmpl.structure?.steps?.length || 0} stages</span>
                        
                        {isMarketplace && isAdmin && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleImportBlueprint(tmpl);
                            }}
                            className="text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer flex items-center space-x-1"
                          >
                            <span>Import Blueprint</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Right side: Blueprint Canvas detail panel */}
        <div className="col-span-1">
          {selectedTemplate ? (
            <div className="glass-panel rounded-2xl p-6 shadow-xl space-y-6 sticky top-6 max-h-[85vh] overflow-y-auto">
              <div className="border-b border-slate-800/60 pb-4">
                <span className="block text-[10px] text-indigo-400 uppercase tracking-widest font-bold mb-1">
                  Blueprint Structure
                </span>
                <h2 className="text-sm font-bold text-white tracking-wide">
                  {selectedTemplate.name}
                </h2>
                <p className="text-[11px] text-slate-400 leading-relaxed mt-1">
                  {selectedTemplate.description}
                </p>
              </div>

              {/* Step checklist preview */}
              <div className="space-y-4">
                <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Workflow Execution Sequence
                </span>

                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {selectedTemplate.structure?.steps?.map((step: any) => (
                    <div key={step.step_order} className="relative">
                      {/* Circle indicator */}
                      <div className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-[8px] text-indigo-400 ring-4 ring-slate-950">
                        {step.step_order}
                      </div>

                      <div className="space-y-1">
                        <span className="block text-xs font-bold text-slate-200">{step.name}</span>
                        <span className="block text-[10px] text-indigo-400 font-medium uppercase tracking-wider">
                          Role Context: {step.approver_role}
                        </span>

                        {step.rule_definition && (
                          <div className="mt-2 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/40 flex items-start space-x-2 text-[9px] text-slate-400 leading-relaxed">
                            <Info className="w-3.5 h-3.5 text-indigo-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <span className="font-bold text-slate-300 block mb-0.5">Rules Engine Logic:</span>
                              {step.rule_definition.conditions?.map((c: any, idx: number) => (
                                <span key={idx} className="block font-mono bg-slate-950 px-1 py-0.5 rounded text-[8px] mt-0.5 text-indigo-300">
                                  IF {c.field} {c.operator} {c.value}
                                </span>
                              ))}
                              <span className="block mt-1 font-semibold text-slate-300">
                                ACTION: {step.rule_definition.action === "ROUTE_TO_ROLE" ? `Route to Executive ${step.rule_definition.action_value || "Admin"}` : step.rule_definition.action}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel rounded-2xl p-12 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-3">
              <BookOpen className="w-8 h-8 text-slate-700 animate-pulse-subtle" />
              <span>Select a template schema to display detailed dynamic routing paths.</span>
            </div>
          )}
        </div>
      </div>

      {/* CREATE BLUEPRINT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-xl glass-panel border border-slate-800 rounded-3xl p-8 space-y-6 shadow-2xl glass-panel-glow max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-800/60 pb-4">
              <h3 className="text-md font-bold text-white tracking-wide">Design Workflow Blueprint</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white text-xs cursor-pointer"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleCreateTemplate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Template Name
                  </label>
                  <input
                    type="text"
                    required
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                    placeholder="e.g. Procurement Hardware Sign-off"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Category Tag
                  </label>
                  <select
                    value={templateCategory}
                    onChange={(e) => setTemplateCategory(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none"
                  >
                    <option value="Procurement">Procurement</option>
                    <option value="Finance">Finance</option>
                    <option value="IT">IT</option>
                    <option value="HR">HR</option>
                    <option value="Compliance">Compliance</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Blueprint Purpose / Description
                </label>
                <textarea
                  value={templateDesc}
                  onChange={(e) => setTemplateDesc(e.target.value)}
                  rows={2}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  placeholder="Summarize the audit target and execution pipeline scope..."
                />
              </div>

              {/* Dynamic Steps Wizard Builder */}
              <div className="border-t border-slate-800/60 pt-4 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">
                    Process Sequence Configuration
                  </span>
                  <button
                    type="button"
                    onClick={handleAddStep}
                    className="text-xs bg-indigo-500/10 hover:bg-indigo-500/25 border border-indigo-500/20 text-indigo-400 font-bold px-3 py-1.5 rounded-lg cursor-pointer transition-all flex items-center space-x-1"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Add Stage Step</span>
                  </button>
                </div>

                <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
                  {steps.map((step, sIdx) => (
                    <div
                      key={sIdx}
                      className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-3 relative"
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-slate-400">Step #{sIdx + 1} Stage</span>
                        {steps.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveStep(sIdx)}
                            className="text-[10px] text-rose-400 hover:text-rose-350 cursor-pointer"
                          >
                            Remove
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-[9px] text-slate-400 uppercase tracking-wider mb-1.5">
                            Step Title
                          </label>
                          <input
                            type="text"
                            required
                            value={step.name}
                            onChange={(e) => handleStepChange(sIdx, "name", e.target.value)}
                            className="w-full bg-slate-950/60 border border-slate-850 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
                          />
                        </div>

                        <div>
                          <label className="block text-[9px] text-slate-400 uppercase tracking-wider mb-1.5">
                            Approver Role Context
                          </label>
                          <select
                            value={step.approver_role}
                            onChange={(e) => handleStepChange(sIdx, "approver_role", e.target.value)}
                            className="w-full bg-slate-950/60 border border-slate-850 rounded-xl px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none"
                          >
                            <option value="Employee">Employee Role</option>
                            <option value="Manager">Manager Role</option>
                            <option value="Admin">Admin Role</option>
                          </select>
                        </div>
                      </div>

                      {/* Toggle Rule */}
                      <div className="pt-1 flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id={`toggle-rule-${sIdx}`}
                          checked={step.rule_definition !== null}
                          onChange={(e) => handleToggleRule(sIdx, e.target.checked)}
                          className="w-3 h-3 text-indigo-650 bg-slate-900 border-slate-850 rounded focus:ring-0 cursor-pointer"
                        />
                        <label
                          htmlFor={`toggle-rule-${sIdx}`}
                          className="text-[9px] font-semibold text-slate-350 uppercase tracking-wide cursor-pointer"
                        >
                          Enable Rules Engine Conditions for this step
                        </label>
                      </div>

                      {/* Rule configuration fields */}
                      {step.rule_definition && (
                        <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-850 space-y-3">
                          <div className="flex justify-between items-center text-[8px] text-indigo-400 uppercase font-bold tracking-wider mb-1">
                            <span>Rules Condition Logic</span>
                          </div>

                          <div className="grid grid-cols-3 gap-2">
                            <div>
                              <label className="block text-[8px] text-slate-500 uppercase tracking-wider mb-1">
                                Field Context
                              </label>
                              <select
                                value={step.rule_definition.conditions[0]?.field || "amount"}
                                onChange={(e) => handleRuleConditionChange(sIdx, 0, "field", e.target.value)}
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-[10px] text-slate-200 focus:outline-none"
                              >
                                <option value="amount">amount ($)</option>
                                <option value="department_code">department_code</option>
                              </select>
                            </div>

                            <div>
                              <label className="block text-[8px] text-slate-500 uppercase tracking-wider mb-1">
                                Operator
                              </label>
                              <select
                                value={step.rule_definition.conditions[0]?.operator || ">"}
                                onChange={(e) => handleRuleConditionChange(sIdx, 0, "operator", e.target.value)}
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-[10px] text-slate-200 focus:outline-none"
                              >
                                <option value=">">&gt; (Greater Than)</option>
                                <option value="<">&lt; (Less Than)</option>
                                <option value="==">== (Equal To)</option>
                                <option value="!=">!= (Not Equal To)</option>
                              </select>
                            </div>

                            <div>
                              <label className="block text-[8px] text-slate-500 uppercase tracking-wider mb-1">
                                Target Value
                              </label>
                              <input
                                type="text"
                                required
                                value={step.rule_definition.conditions[0]?.value || ""}
                                onChange={(e) => handleRuleConditionChange(sIdx, 0, "value", e.target.value)}
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-[10px] text-slate-200 focus:outline-none"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4 border-t border-slate-900/60 pt-2.5">
                            <div>
                              <label className="block text-[8px] text-slate-500 uppercase tracking-wider mb-1">
                                Action Outcome
                              </label>
                              <select
                                value={step.rule_definition.action}
                                onChange={(e) => handleRuleActionChange(sIdx, "action", e.target.value)}
                                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-[10px] text-slate-200 focus:outline-none"
                              >
                                <option value="ROUTE_TO_ROLE">ROUTE_TO_ROLE</option>
                                <option value="SKIP_STEP">SKIP_STEP</option>
                                <option value="AUTO_APPROVE">AUTO_APPROVE</option>
                              </select>
                            </div>

                            {step.rule_definition.action === "ROUTE_TO_ROLE" && (
                              <div>
                                <label className="block text-[8px] text-slate-500 uppercase tracking-wider mb-1">
                                  Target Role
                                </label>
                                <select
                                  value={step.rule_definition.action_value || "Admin"}
                                  onChange={(e) => handleRuleActionChange(sIdx, "action_value", e.target.value)}
                                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2 py-1 text-[10px] text-slate-200 focus:outline-none"
                                >
                                  <option value="Admin">Admin</option>
                                  <option value="Manager">Manager</option>
                                  <option value="Employee">Employee</option>
                                </select>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-indigo-650 hover:bg-indigo-600 text-white font-semibold text-xs tracking-wider py-3 rounded-xl shadow-lg cursor-pointer transition-all flex items-center justify-center space-x-2"
              >
                <Sliders className="w-4 h-4" />
                <span>Save Blueprint Template</span>
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default Templates;
