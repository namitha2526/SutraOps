from datetime import datetime
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import StructuredLogger
from app.models.approval import Approval, Task
from app.models.workflow import Workflow
from app.models.system import Notification
from app.models.user import User

@celery_app.task(name="app.tasks.check_sla_deadlines")
def check_sla_deadlines():
    """
    Background worker cron task checking active step approvals for SLA breaches.
    Escalates workflow states to 'Escalated', marks task cards as 'Urgent',
    and registers system database alert notifications.
    """
    StructuredLogger.info("Starting background audit scanner for active SLA deadlines...")
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        # Query pending approvals that have breached their SLA deadlines
        breached_approvals = db.query(Approval).filter(
            Approval.status == "Pending",
            Approval.sla_deadline.isnot(None),
            Approval.sla_deadline < now
        ).all()

        if not breached_approvals:
            StructuredLogger.info("SLA check complete: 0 active approvals breached.")
            return

        StructuredLogger.warning(f"SLA Scanner detected {len(breached_approvals)} breached approvals.")
        
        for approval in breached_approvals:
            # 1. Update Approval status to Escalated (or note in workflow)
            workflow = db.query(Workflow).filter(Workflow.id == approval.workflow_id).first()
            if workflow and workflow.status != "Escalated":
                StructuredLogger.warning(
                    f"Escalating workflow '{workflow.title}' (ID: {workflow.id}) due to SLA breach on step '{approval.step.name}'."
                )
                workflow.status = "Escalated"
                db.add(workflow)
                
                # 2. Find associated Kanban tasks and update priority to Urgent
                tasks = db.query(Task).filter(
                    Task.workflow_id == workflow.id,
                    Task.status.in_(["Todo", "InProgress", "InReview"])
                ).all()
                for task in tasks:
                    task.priority = "Urgent"
                    db.add(task)

                # 3. Create Notification alerts for target users of the step
                target_users_query = db.query(User).filter(
                    User.organization_id == workflow.organization_id,
                    User.is_active.is_(True)
                )
                if approval.step.approver_role:
                    target_users_query = target_users_query.filter(User.role == approval.step.approver_role)
                
                target_users = target_users_query.all()
                for user in target_users:
                    notification = Notification(
                        user_id=user.id,
                        title="SLA Breach Alert",
                        message=f"Urgent: Workflow '{workflow.title}' has breached its SLA on step '{approval.step.name}'!",
                        type="Escalation_Alert",
                        is_read=False
                    )
                    db.add(notification)

        db.commit()
        StructuredLogger.info("SLA escalation batch committed successfully.")
    except Exception as e:
        db.rollback()
        StructuredLogger.error(f"SLA deadlines background scan task failed: {str(e)}")
        raise e
    finally:
        db.close()
