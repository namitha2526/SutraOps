from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.workflow import Workflow, WorkflowStep, WorkflowTemplate
from app.repositories.base import BaseRepository


class WorkflowTemplateRepository(BaseRepository[WorkflowTemplate]):
    def get_marketplace_templates(self, db: Session) -> List[WorkflowTemplate]:
        """
        Retrieves all templates: both public marketplace templates (organization_id is NULL)
        and custom organization templates.
        """
        tenant_id = self._get_tenant_id()
        if tenant_id:
            # Matches public OR specific tenant templates
            return db.query(self.model).filter(
                (self.model.organization_id == tenant_id) | (self.model.organization_id.is_(None))
            ).filter(self.model.is_active.is_(True)).all()
            
        return db.query(self.model).filter(self.model.organization_id.is_(None)).filter(self.model.is_active.is_(True)).all()


class WorkflowRepository(BaseRepository[Workflow]):
    def get_by_creator(self, db: Session, creator_id: UUID) -> List[Workflow]:
        """
        Fetches all workflows initialized by a specific user.
        """
        query = db.query(self.model).filter(self.model.creator_id == creator_id)
        query = self._apply_tenant_filter(query, db)
        return query.all()

    def get_pending_workflows(self, db: Session) -> List[Workflow]:
        """
        Fetches active processing workflows (status 'Pending' or 'Escalated').
        """
        query = db.query(self.model).filter(self.model.status.in_(["Pending", "Escalated"]))
        query = self._apply_tenant_filter(query, db)
        return query.all()


class WorkflowStepRepository(BaseRepository[WorkflowStep]):
    def get_steps_for_workflow(self, db: Session, workflow_id: UUID) -> List[WorkflowStep]:
        """
        Fetches sequence steps for a workflow instance ordered by step_order.
        """
        return db.query(self.model).filter(
            self.model.workflow_id == workflow_id
        ).order_by(self.model.step_order).all()


template_repo = WorkflowTemplateRepository(WorkflowTemplate)
workflow_repo = WorkflowRepository(Workflow)
step_repo = WorkflowStepRepository(WorkflowStep)
