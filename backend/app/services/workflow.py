from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.events import Event, EventBus
from app.core.logging import StructuredLogger
from app.middleware.error_handler import NexusFlowException, ResourceNotFound
from app.models.tenant import Department
from app.models.user import User
from app.models.workflow import Workflow, WorkflowStep, WorkflowTemplate
from app.models.approval import Approval, Task
from app.repositories.workflow import workflow_repo, template_repo, step_repo
from app.schemas.workflow import WorkflowCreate
from app.services.rules_engine import RulesEngine


class WorkflowService:
    """
    Core Domain Service managing the complete workflow lifecycle, sequential transitions,
    dynamic rules-engine evaluations, and event bus pub/sub dispatches.
    """
    
    @staticmethod
    def create_workflow(db: Session, creator: User, req: WorkflowCreate) -> Workflow:
        StructuredLogger.info(
            f"Initializing workflow request: '{req.title}' (Creator: {creator.email})"
        )

        steps_data: List[Dict[str, Any]] = []

        # 1. Resolve steps from Template if selected
        if req.template_id:
            template = template_repo.get(db, req.template_id)
            if not template:
                raise ResourceNotFound(f"Selected workflow template '{req.template_id}' not found")
            
            # Unpack steps structure from JSON template
            # Expected structure schema: {"steps": [{"name": "Step A", "approver_role": "Manager", "rule_definition": {...}}]}
            steps_data = template.structure.get("steps", [])
        elif req.steps:
            # Manually configured custom steps
            for idx, s in enumerate(req.steps):
                steps_data.append({
                    "name": s.name,
                    "step_order": s.step_order or (idx + 1),
                    "approver_role": s.approver_role,
                    "approver_id": str(s.approver_id) if s.approver_id else None,
                    "rule_definition": s.rule_definition.dict() if s.rule_definition else None
                })
        else:
            raise NexusFlowException(
                message="Workflow creation requires either a valid template_id or a manual steps array definition"
            )

        if not steps_data:
            raise NexusFlowException(message="Workflow must contain at least one step sequence")

        # 2. Write Workflow Document
        workflow_obj = Workflow(
            organization_id=creator.organization_id,
            creator_id=creator.id,
            template_id=req.template_id,
            title=req.title,
            description=req.description,
            status="Draft",
            version_id=1
        )
        db.add(workflow_obj)
        db.flush()

        # 3. Write Step configurations
        for idx, step_item in enumerate(steps_data):
            step = WorkflowStep(
                workflow_id=workflow_obj.id,
                name=step_item.get("name"),
                step_order=step_item.get("step_order", idx + 1),
                approver_role=step_item.get("approver_role", "Manager"),
                approver_id=step_item.get("approver_id"),
                rule_definition=step_item.get("rule_definition")
            )
            db.add(step)

        try:
            db.commit()
            db.refresh(workflow_obj)
            StructuredLogger.info(f"Workflow Draft '{workflow_obj.title}' created (ID: {workflow_obj.id})")
        except Exception as e:
            db.rollback()
            StructuredLogger.error(f"Failed to create workflow: {str(e)}")
            raise NexusFlowException("Database error saving workflow configurations")

        # 4. Auto-Publish Event: workflow.created
        event = Event(
            event_type="workflow.created",
            payload={
                "workflow_id": str(workflow_obj.id),
                "title": workflow_obj.title,
                "context_data": req.context_data
            },
            organization_id=workflow_obj.organization_id
        )
        asyncio_loop = None
        try:
            import asyncio
            asyncio.create_task(EventBus.publish(event))
        except RuntimeError:
            # Gracefully handle running events outside event loop threads (like initial test seeds)
            pass

        return workflow_obj

    @classmethod
    def start_processing(cls, db: Session, workflow_id: UUID, context_data: Dict[str, Any]) -> Workflow:
        """
        Transitions a Draft workflow into processing, evaluating dynamic steps sequentially.
        """
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ResourceNotFound("Workflow instance not found")

        if workflow.status != "Draft":
            raise NexusFlowException("Only Draft workflows can be initiated into processing")

        workflow.status = "Pending"
        db.add(workflow)
        db.flush()

        cls.evaluate_next_step(db, workflow, context_data)
        return workflow

    @classmethod
    def evaluate_next_step(
        cls,
        db: Session,
        workflow: Workflow,
        context_data: Dict[str, Any]
    ):
        """
        Evaluates step queues, processing rules-engine skips recursively.
        """
        steps = step_repo.get_steps_for_workflow(db, workflow.id)
        if not steps:
            # Empty steps pipeline - auto-approve complete workflow
            cls._finalize_workflow(db, workflow, "Approved")
            return

        # Find first step that is not yet completed or actioned
        target_step: Optional[WorkflowStep] = None
        for step in steps:
            # Check if there is already an approved/completed approval for this step
            existing_approval = db.query(Approval).filter(
                Approval.workflow_id == workflow.id,
                Approval.step_id == step.id
            ).first()

            if not existing_approval or existing_approval.status == "Pending":
                target_step = step
                break

        if not target_step:
            # All steps completed successfully! Finalize process
            cls._finalize_workflow(db, workflow, "Approved")
            return

        # 2. Check if this step has dynamic conditions
        rule_override = RulesEngine.evaluate_step_rule(
            target_step.rule_definition,
            context_data
        )

        if rule_override:
            action = rule_override.get("action")
            action_val = rule_override.get("action_value")

            if action == "SKIP_STEP":
                StructuredLogger.info(f"Rules Engine: Step '{target_step.name}' skipped by condition matching.")
                # Create an approved record indicating skip
                skip_approval = Approval(
                    workflow_id=workflow.id,
                    step_id=target_step.id,
                    status="Approved",
                    comments="Bypassed: skipped by dynamic rules engine",
                    sla_deadline=datetime.utcnow() + timedelta(days=2),
                    actioned_at=datetime.utcnow()
                )
                db.add(skip_approval)
                db.commit()
                # Recursively evaluate the subsequent step
                cls.evaluate_next_step(db, workflow, context_data)
                return

            elif action == "AUTO_APPROVE":
                StructuredLogger.info(f"Rules Engine: Step '{target_step.name}' auto-approved by condition matching.")
                auto_approval = Approval(
                    workflow_id=workflow.id,
                    step_id=target_step.id,
                    status="Approved",
                    comments="Auto-Approved: executed by dynamic rules engine",
                    sla_deadline=datetime.utcnow() + timedelta(days=2),
                    actioned_at=datetime.utcnow()
                )
                db.add(auto_approval)
                db.commit()
                # Recursively evaluate subsequent step
                cls.evaluate_next_step(db, workflow, context_data)
                return

            elif action == "ROUTE_TO_ROLE":
                # Route step to custom override role instead of default config role
                target_step.approver_role = action_val
                db.add(target_step)
                db.flush()
                StructuredLogger.info(
                    f"Rules Engine: Re-routing step '{target_step.name}' to custom override role: {action_val}"
                )

        # 3. Create normal Pending Approval assignment
        # Look up existing pending to avoid double creation
        pending = db.query(Approval).filter(
            Approval.workflow_id == workflow.id,
            Approval.step_id == target_step.id,
            Approval.status == "Pending"
        ).first()

        if not pending:
            # Calculate standard SLA deadline (e.g., 3 days)
            sla_date = datetime.utcnow() + timedelta(days=3)
            
            # Resolve specific approver if direct approver_id was declared
            pending = Approval(
                workflow_id=workflow.id,
                step_id=target_step.id,
                approver_id=target_step.approver_id,
                status="Pending",
                sla_deadline=sla_date
            )
            db.add(pending)
            
        workflow.current_step_id = target_step.id
        db.add(workflow)
        
        try:
            db.commit()
            StructuredLogger.info(
                f"Step Assigned: Step '{target_step.name}' is now active (Role: {target_step.approver_role})"
            )
        except Exception as e:
            db.rollback()
            StructuredLogger.error(f"Failed setting step: {str(e)}")
            return

        # 4. Trigger Task & Notification Event Dispatch
        event = Event(
            event_type="task.assigned",
            payload={
                "workflow_id": str(workflow.id),
                "step_id": str(target_step.id),
                "approval_id": str(pending.id),
                "role_target": target_step.approver_role,
                "specific_user": str(target_step.approver_id) if target_step.approver_id else None,
                "title": f"Approval Pending: {workflow.title} - Step {target_step.name}"
            },
            organization_id=workflow.organization_id
        )
        try:
            import asyncio
            asyncio.create_task(EventBus.publish(event))
        except RuntimeError:
            pass

    @staticmethod
    def _finalize_workflow(db: Session, workflow: Workflow, final_status: str):
        """
        Concludes workflow execution, setting final outcomes (Approved / Rejected).
        """
        workflow.status = final_status
        workflow.current_step_id = None
        db.add(workflow)
        db.commit()
        
        StructuredLogger.info(
            f"WORKFLOW CONCLUDED: Workflow '{workflow.title}' finalized as: {final_status}"
        )
        
        # Dispatch completion event
        event = Event(
            event_type="workflow.completed" if final_status == "Approved" else "workflow.rejected",
            payload={
                "workflow_id": str(workflow.id),
                "title": workflow.title,
                "creator_id": str(workflow.creator_id),
                "status": final_status
            },
            organization_id=workflow.organization_id
        )
        try:
            import asyncio
            asyncio.create_task(EventBus.publish(event))
        except RuntimeError:
            pass
