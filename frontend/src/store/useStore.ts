import { create } from "zustand";
import { api } from "../services/api";

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id: string;
  department?: {
    id: string;
    name: string;
    code: string;
  };
}

interface WorkflowInstance {
  id: string;
  title: string;
  description: string;
  status: string;
  current_step_id: string | null;
  version_id: number;
  created_at: string;
  updated_at: string;
  creator: {
    full_name: string;
    email: string;
  };
}

interface TaskInstance {
  id: string;
  workflow_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  assignee_id: string | null;
  deadline: string | null;
}

interface ApprovalInstance {
  id: string;
  workflow_id: string;
  status: string;
  sla_deadline: string | null;
  workflow: WorkflowInstance;
  step: {
    name: string;
    approver_role: string;
  };
}

interface NotificationInstance {
  id: string;
  title: string;
  message: string;
  is_read: boolean;
  type: string;
  created_at: string;
}

interface AppStore {
  user: UserProfile | null;
  organizationId: string | null;
  workflows: WorkflowInstance[];
  pendingApprovals: ApprovalInstance[];
  tasks: TaskInstance[];
  notifications: NotificationInstance[];
  analytics: any | null;
  isLoading: boolean;
  
  // Setters & Authentications
  setSession: (accessToken: string, refreshToken: string, orgId: string) => void;
  clearSession: () => void;
  loadUserProfile: () => Promise<void>;
  
  // Queries
  fetchWorkflows: () => Promise<void>;
  fetchApprovals: () => Promise<void>;
  fetchTasks: () => Promise<void>;
  fetchNotifications: () => Promise<void>;
  fetchAnalytics: () => Promise<void>;
  
  // Optimistic Mutations
  updateTaskStatus: (taskId: string, newStatus: string) => Promise<void>;
  actionStepApproval: (approvalId: string, status: string, comments?: string) => Promise<void>;
}

export const useStore = create<AppStore>((set, get) => ({
  user: null,
  organizationId: localStorage.getItem("organization_id"),
  workflows: [],
  pendingApprovals: [],
  tasks: [],
  notifications: [],
  analytics: null,
  isLoading: false,

  setSession: (accessToken: string, refreshToken: string, orgId: string) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("organization_id", orgId);
    set({ organizationId: orgId });
  },

  clearSession: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("organization_id");
    set({ user: null, organizationId: null, workflows: [], pendingApprovals: [], tasks: [], notifications: [], analytics: null });
  },

  loadUserProfile: async () => {
    try {
      const response = await api.get("/auth/me");
      set({ user: response.data, organizationId: response.data.organization_id });
      localStorage.setItem("organization_id", response.data.organization_id);
    } catch (error) {
      get().clearSession();
    }
  },

  fetchWorkflows: async () => {
    try {
      set({ isLoading: true });
      const response = await api.get("/workflows");
      set({ workflows: response.data, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
    }
  },

  fetchApprovals: async () => {
    try {
      const response = await api.get("/approvals/pending");
      set({ pendingApprovals: response.data });
    } catch (error) {}
  },

  fetchTasks: async () => {
    try {
      const response = await api.get("/approvals/tasks");
      set({ tasks: response.data });
    } catch (error) {}
  },

  fetchNotifications: async () => {
    try {
      const response = await api.get("/approvals/pending"); // Defaulting pending approval check as in-app notification context
      const notifs: NotificationInstance[] = response.data.map((app: any) => ({
        id: app.id,
        title: "Action Item Assigned",
        message: `Workflow "${app.workflow.title}" is pending your review for step "${app.step.name}"`,
        is_read: false,
        type: "Approval_Request",
        created_at: app.created_at || new Date().toISOString()
      }));
      set({ notifications: notifs });
    } catch (error) {}
  },

  fetchAnalytics: async () => {
    try {
      const response = await api.get("/analytics");
      set({ analytics: response.data });
    } catch (error) {}
  },

  // Optimistic Kanban Board card transition updates
  updateTaskStatus: async (taskId: string, newStatus: string) => {
    const originalTasks = get().tasks;
    
    // 1. Instantly transition status card optimistically
    const optimsiticTasks = originalTasks.map((t) => 
      t.id === taskId ? { ...t, status: newStatus } : t
    );
    set({ tasks: optimsiticTasks });

    try {
      // 2. Execute background database synchronization
      await api.put(`/approvals/tasks/${taskId}/status?status=${newStatus}`);
    } catch (error) {
      // 3. Rollback state immediately on failure
      set({ tasks: originalTasks });
    }
  },

  actionStepApproval: async (approvalId: string, status: string, comments?: string) => {
    try {
      await api.post(`/approvals/${approvalId}/action`, { status, comments });
      // Clear sign-off from lists and sync lists
      get().fetchApprovals();
      get().fetchWorkflows();
      get().fetchAnalytics();
    } catch (error) {
      throw error;
    }
  }
}));
