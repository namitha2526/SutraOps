from typing import Dict, Any
from uuid import UUID
from app.core.database import SessionLocal
from app.core.events import Event, EventBus
from app.core.logging import StructuredLogger
from app.models.approval import Task, Approval
from app.models.system import Notification, AuditLog
from app.models.user import User
from app.models.workflow import Workflow
from app.services.workflow import WorkflowService


# =====================================================================
# Callback Handlers
# =====================================================================

async def handle_workflow_created(event: Event):
    """
    Subscribed to 'workflow.created'. Automatically starts the step execution pipeline.
    """
    workflow_id_str = event.payload.get("workflow_id")
    context_data = event.payload.get("context_data", {})
    
    if not workflow_id_str:
        return
        
    StructuredLogger.info(f"Event handler: initiating processing for workflow {workflow_id_str}")
    
    db = SessionLocal()
    try:
        workflow_id = UUID(workflow_id_str)
        # Call service to transition Draft -> Pending and evaluate first rules step
        WorkflowService.start_processing(db, workflow_id, context_data)
    except Exception as e:
        StructuredLogger.error(f"Error executing handle_workflow_created: {str(e)}")
        raise e
    finally:
        db.close()


async def handle_task_assigned(event: Event):
    """
    Subscribed to 'task.assigned'. 
    1. Generates a Task record in the DB for the target assignee/role (to show on Kanban board).
    2. Writes a Notification log for all users matching the target role in this organization.
    """
    workflow_id_str = event.payload.get("workflow_id")
    approval_id_str = event.payload.get("approval_id")
    role_target = event.payload.get("role_target")
    specific_user_id = event.payload.get("specific_user")
    title = event.payload.get("title", "Approval Pending")

    if not workflow_id_str or not approval_id_str:
        return

    db = SessionLocal()
    try:
        workflow_id = UUID(workflow_id_str)
        approval_id = UUID(approval_id_str)

        # 1. Create matching Kanban Task
        # Look up if assignee_id is direct
        assignee_id = UUID(specific_user_id) if specific_user_id else None
        
        # If no specific user assignee was declared, resolve the first active user matching target role in org
        if not assignee_id and role_target:
            matching_user = db.query(User).filter(
                User.organization_id == event.organization_id,
                User.role == role_target,
                User.is_active.is_(True)
            ).first()
            if matching_user:
                assignee_id = matching_user.id

        task = Task(
            workflow_id=workflow_id,
            title=title,
            description=f"Action required on workflow: please review details for step.",
            status="Todo",
            priority="Medium",
            assignee_id=assignee_id
        )
        db.add(task)

        # 2. Write Database Notification alerts for target users
        target_users_query = db.query(User).filter(
            User.organization_id == event.organization_id,
            User.is_active.is_(True)
        )
        if specific_user_id:
            target_users_query = target_users_query.filter(User.id == UUID(specific_user_id))
        elif role_target:
            target_users_query = target_users_query.filter(User.role == role_target)

        target_users = target_users_query.all()
        
        for user in target_users:
            notification = Notification(
                user_id=user.id,
                title="New Task Assigned",
                message=title,
                type="Approval_Request",
                is_read=False
            )
            db.add(notification)

        db.commit()
        StructuredLogger.info(
            f"Task and notifications generated for step approval {approval_id_str}. Alerts sent to {len(target_users)} users."
        )
    except Exception as e:
        db.rollback()
        StructuredLogger.error(f"Error executing handle_task_assigned: {str(e)}")
        raise e
    finally:
        db.close()


async def handle_workflow_concluded(event: Event):
    """
    Subscribed to 'workflow.completed' or 'workflow.rejected'.
    1. Generates an Audit Log entry tracking action parameters.
    2. Alerts creator of final decision.
    """
    workflow_id_str = event.payload.get("workflow_id")
    creator_id_str = event.payload.get("creator_id")
    title = event.payload.get("title")
    status = event.payload.get("status")

    if not workflow_id_str or not creator_id_str:
        return

    db = SessionLocal()
    try:
        workflow_id = UUID(workflow_id_str)
        creator_id = UUID(creator_id_str)

        # 1. Create Audit trail
        audit = AuditLog(
            organization_id=event.organization_id,
            user_id=creator_id,
            workflow_id=workflow_id,
            action="Conclude_Workflow",
            entity_name="workflows",
            entity_id=workflow_id,
            payload={"status": status, "title": title}
        )
        db.add(audit)

        # 2. Alert Creator
        notification = Notification(
            user_id=creator_id,
            title="Workflow Finalized",
            message=f"Your workflow request '{title}' has been successfully {status}!",
            type="Workflow_Update",
            is_read=False
        )
        db.add(notification)

        db.commit()
        StructuredLogger.info(f"Concluded audit log and creator alert successfully logged for {workflow_id_str}")
    except Exception as e:
        db.rollback()
        StructuredLogger.error(f"Error executing handle_workflow_concluded: {str(e)}")
        raise e
    finally:
        db.close()


# =====================================================================
# Registration Function
# =====================================================================

def register_all_listeners():
    """
    Hooks all event callbacks up to EventBus channel bindings on startup.
    """
    EventBus.subscribe("workflow.created", handle_workflow_created)
    EventBus.subscribe("task.assigned", handle_task_assigned)
    EventBus.subscribe("workflow.completed", handle_workflow_concluded)
    EventBus.subscribe("workflow.rejected", handle_workflow_concluded)
    StructuredLogger.info("Event-driven listeners successfully wired on EventBus channels")
