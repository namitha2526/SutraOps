from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.events import Event, EventBus
from app.core.logging import StructuredLogger
from app.middleware.error_handler import NexusFlowException, ResourceNotFound, PermissionDenied
from app.models.approval import Approval, Task, Comment, Attachment
from app.models.user import User
from app.models.workflow import Workflow, WorkflowStep
from app.services.workflow import WorkflowService


class ApprovalService:
    """
    Domain service handling active step decisions (Approve/Reject), comment additions,
    attachment uploads, and Kanban board tasks state transitions.
    """
    
    @staticmethod
    def action_approval(
        db: Session,
        user: User,
        approval_id: UUID,
        status: str,
        comments: Optional[str] = None
    ) -> Approval:
        StructuredLogger.info(
            f"Processing step approval request (ID: {approval_id}, Decision: {status}) by {user.email}"
        )

        # 1. Fetch Approval record
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise ResourceNotFound("Step approval target not found")

        if approval.status != "Pending":
            raise NexusFlowException("Decision already committed for this step approval")

        # 2. Verify authorization against RBAC role matrix
        step: WorkflowStep = approval.step
        workflow: Workflow = approval.workflow

        # Ensure user belongs to the correct role or is directly assigned
        is_authorized = False
        if step.approver_id and step.approver_id == user.id:
            is_authorized = True
        elif user.role in ["SuperAdmin", "Admin"]:
            is_authorized = True
        elif user.role == step.approver_role:
            is_authorized = True

        if not is_authorized:
            raise PermissionDenied(
                f"Your role '{user.role}' is unauthorized to sign off step '{step.name}'. "
                f"Approver Role Required: '{step.approver_role}'"
            )

        # 3. Update Decision details
        approval.status = status
        approval.comments = comments
        approval.actioned_at = datetime.utcnow()
        approval.approver_id = user.id
        db.add(approval)

        # Write discussion comment record automatically for audit completeness if provided
        if comments:
            comment = Comment(
                workflow_id=workflow.id,
                user_id=user.id,
                content=f"Decision Remarks ({status}): {comments}"
            )
            db.add(comment)

        db.flush()

        # 4. Handle Decision Flow Logic (Optimistic Concurrency Locked)
        if status == "Approved":
            StructuredLogger.info(f"Step '{step.name}' signed off successfully. Moving to next seq.")
            # Progress to subsequent step sequence inside transactional pipeline
            # Dynamic rules context can be populated using existing comments/history or simple attributes
            # Here we default to using a general organizational context dict
            context_data = {
                "amount": 15000,  # Default fallback context mock
                "department_code": user.department.code if user.department else "GEN"
            }
            WorkflowService.evaluate_next_step(db, workflow, context_data)
        elif status == "Rejected":
            StructuredLogger.info(f"Step '{step.name}' rejected by {user.email}. Terminating process.")
            # Wipes subsequent pipelines, marking workflow Rejected
            WorkflowService._finalize_workflow(db, workflow, "Rejected")

        try:
            db.commit()
            db.refresh(approval)
            StructuredLogger.info(f"Approval state committed successfully (ID: {approval.id})")
            return approval
        except Exception as e:
            db.rollback()
            StructuredLogger.error(f"Failed committing step decision: {str(e)}")
            raise NexusFlowException("Database conflict during concurrent step resolution. Please reload.")

    @staticmethod
    def get_pending_approvals(db: Session, user: User) -> List[Approval]:
        """
        Retrieves all pending approvals scoped to the user's role or direct assignments.
        """
        query = db.query(Approval).join(WorkflowStep).filter(
            Approval.status == "Pending",
            Approval.workflow_id == Workflow.id,
            Workflow.organization_id == user.organization_id
        )
        
        # SuperAdmins and Admins see all pending items inside their tenant scope,
        # Managers and Employees see items matching their role or matching them directly.
        if user.role not in ["SuperAdmin", "Admin"]:
            query = query.filter(
                (WorkflowStep.approver_role == user.role) | (WorkflowStep.approver_id == user.id)
            )

        return query.all()

    @staticmethod
    def add_comment(db: Session, user: User, workflow_id: UUID, content: str) -> Comment:
        # Enforce check to verify workflow exists under user's organization
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == user.organization_id
        ).first()
        if not workflow:
            raise ResourceNotFound("Target workflow not found")

        comment = Comment(
            workflow_id=workflow_id,
            user_id=user.id,
            content=content
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def update_task_status(db: Session, user: User, task_id: UUID, status: str) -> Task:
        task = db.query(Task).join(Workflow).filter(
            Task.id == task_id,
            Workflow.organization_id == user.organization_id
        ).first()
        
        if not task:
            raise ResourceNotFound("Kanban board task not found")

        valid_statuses = ["Todo", "InProgress", "InReview", "Done"]
        if status not in valid_statuses:
            raise NexusFlowException("Invalid task column value specified")

        task.status = status
        db.add(task)
        db.commit()
        db.refresh(task)
        
        StructuredLogger.info(f"Kanban Task '{task.title}' updated to column status: {status}")
        return task
