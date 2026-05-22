import sys
from datetime import datetime, timedelta
from uuid import UUID, uuid4

# Insert workspace path to allow running directly from project root
sys.path.append(".")

from app.core.database import Base, engine, SessionLocal
from app.core.logging import StructuredLogger
from app.core.security import get_password_hash
from app.models.tenant import Organization, Department
from app.models.user import User
from app.models.workflow import WorkflowTemplate, Workflow, WorkflowStep
from app.models.approval import Approval, Task, Comment, Attachment
from app.models.system import Notification, AuditLog


def seed_database():
    StructuredLogger.info("Starting database initialization schema generation...")
    # Instantly builds database schemas on SQLite/PostgreSQL
    Base.metadata.create_all(bind=engine)
    StructuredLogger.info("Database schemas generated successfully.")

    db = SessionLocal()
    try:
        # Check if already seeded
        existing_org = db.query(Organization).filter(Organization.domain == "sutraops.com").first()
        if existing_org:
            StructuredLogger.warning("Tenant 'sutraops.com' already seeded. Skipping seeder runtime.")
            return

        StructuredLogger.info("Seeding enterprise workspace tenant metadata...")
        
        # 1. Seed Organization
        org = Organization(
            name="SutraOps Corp",
            domain="sutraops.com",
            is_active=True
        )
        db.add(org)
        db.flush()

        # 2. Seed Departments
        exec_dept = Department(organization_id=org.id, name="Executive Management", code="EXEC")
        fin_dept = Department(organization_id=org.id, name="Finance & Accounting", code="FIN")
        hr_dept = Department(organization_id=org.id, name="Human Resources", code="HR")
        it_dept = Department(organization_id=org.id, name="Information Technology", code="IT")
        
        db.add(exec_dept)
        db.add(fin_dept)
        db.add(hr_dept)
        db.add(it_dept)
        db.flush()

        # 3. Seed Role-based Accounts
        pw_hash = get_password_hash("password123")
        
        admin = User(
            organization_id=org.id,
            department_id=exec_dept.id,
            email="admin@sutraops.com",
            hashed_password=pw_hash,
            full_name="Alice Admin",
            role="Admin",
            is_active=True
        )
        manager = User(
            organization_id=org.id,
            department_id=fin_dept.id,
            email="manager@sutraops.com",
            hashed_password=pw_hash,
            full_name="Bob Manager",
            role="Manager",
            is_active=True
        )
        employee = User(
            organization_id=org.id,
            department_id=it_dept.id,
            email="employee@sutraops.com",
            hashed_password=pw_hash,
            full_name="Charlie Employee",
            role="Employee",
            is_active=True
        )

        db.add(admin)
        db.add(manager)
        db.add(employee)
        db.flush()

        StructuredLogger.info("Seeding Workflow Templates marketplace blueprints...")

        # 4. Seed Reusable Marketplace Templates
        expense_structure = {
            "steps": [
                {
                    "name": "Department Manager Review",
                    "step_order": 1,
                    "approver_role": "Manager",
                    "rule_definition": {
                        "conditions": [
                            {"field": "amount", "operator": ">", "value": 5000}
                        ],
                        "action": "ROUTE_TO_ROLE",
                        "action_value": "Admin"  # Route to executive admin for approval if high cost!
                    }
                },
                {
                    "name": "Finance Director Sign-off",
                    "step_order": 2,
                    "approver_role": "Admin",
                    "rule_definition": None
                }
            ]
        }
        
        expense_tmpl = WorkflowTemplate(
            organization_id=None,  # Available to all orgs as a public marketplace pre-built
            name="Capital Expense Reimbursement",
            description="Multi-step sign-off process for expense items with dynamic high-value rules triggers.",
            category="Finance",
            structure=expense_structure,
            is_active=True
        )
        
        software_structure = {
            "steps": [
                {
                    "name": "IT Administrator Provisioning",
                    "step_order": 1,
                    "approver_role": "Admin",
                    "rule_definition": {
                        "conditions": [
                            {"field": "department_code", "operator": "==", "value": "EXEC"}
                        ],
                        "action": "SKIP_STEP"  # Bypasses IT check for executives
                    }
                }
            ]
        }
        
        software_tmpl = WorkflowTemplate(
            organization_id=org.id,  # Scoped specifically as a custom tenant template
            name="IT Software License Request",
            description="Onboard licenses (Slack, GitHub Enterprise, Zoom). Bypasses step review for Executives.",
            category="IT",
            structure=software_structure,
            is_active=True
        )

        db.add(expense_tmpl)
        db.add(software_tmpl)
        db.flush()

        StructuredLogger.info("Seeding transactional records and workflows sandbox...")

        # 5. Seed active process workflows
        # Workflow A: Completed & Approved Expense
        wf_completed = Workflow(
            organization_id=org.id,
            creator_id=employee.id,
            template_id=expense_tmpl.id,
            title="Q2 Marketing Campaign Tools Purchase",
            description="Reimburse costs for visual design subscriptions ($1200).",
            status="Approved",
            version_id=1
        )
        db.add(wf_completed)
        db.flush()

        step_a1 = WorkflowStep(
            workflow_id=wf_completed.id,
            name="Department Manager Review",
            step_order=1,
            approver_role="Manager"
        )
        step_a2 = WorkflowStep(
            workflow_id=wf_completed.id,
            name="Finance Director Sign-off",
            step_order=2,
            approver_role="Admin"
        )
        db.add(step_a1)
        db.add(step_a2)
        db.flush()

        app_a1 = Approval(
            workflow_id=wf_completed.id,
            step_id=step_a1.id,
            approver_id=manager.id,
            status="Approved",
            comments="Verified budget availability. Approved.",
            sla_deadline=datetime.utcnow() - timedelta(days=2),
            actioned_at=datetime.utcnow() - timedelta(days=3)
        )
        app_a2 = Approval(
            workflow_id=wf_completed.id,
            step_id=step_a2.id,
            approver_id=admin.id,
            status="Approved",
            comments="Final signoff executed.",
            sla_deadline=datetime.utcnow() - timedelta(days=1),
            actioned_at=datetime.utcnow() - timedelta(hours=6)
        )
        db.add(app_a1)
        db.add(app_a2)

        # Workflow B: Active Pending sign-off
        wf_pending = Workflow(
            organization_id=org.id,
            creator_id=employee.id,
            template_id=expense_tmpl.id,
            title="Server Hardware Expansion Reimbursement",
            description="Reimburse hardware parts ($8500). High value matches routing rules!",
            status="Pending",
            version_id=1
        )
        db.add(wf_pending)
        db.flush()

        step_b1 = WorkflowStep(
            workflow_id=wf_pending.id,
            name="Department Manager Review",
            step_order=1,
            approver_role="Manager",
            rule_definition=expense_structure["steps"][0]["rule_definition"]
        )
        db.add(step_b1)
        db.flush()

        # Step 1 was auto-routed to Admin instead of Manager because amount ($8500) > $5000!
        app_b1 = Approval(
            workflow_id=wf_pending.id,
            step_id=step_b1.id,
            status="Pending",
            sla_deadline=datetime.utcnow() + timedelta(days=3)
        )
        db.add(app_b1)
        
        # Associate pending Kanban Task
        task_b1 = Task(
            workflow_id=wf_pending.id,
            title="Review high-value Server Hardware purchase request ($8500)",
            description="Review requested and routed based on amount rules criteria.",
            status="Todo",
            priority="High",
            assignee_id=admin.id
        )
        db.add(task_b1)

        # 6. Seed Comments & Attachments
        comment_1 = Comment(
            workflow_id=wf_pending.id,
            user_id=employee.id,
            content="Attached is the hardware invoice from vendor."
        )
        attachment_1 = Attachment(
            workflow_id=wf_pending.id,
            user_id=employee.id,
            file_name="invoice_hardware.pdf",
            file_url="/static/invoice_hardware.pdf",
            file_size=245000,
            mime_type="application/pdf"
        )
        db.add(comment_1)
        db.add(attachment_1)

        # 7. Seed Notifications and Audits
        notif_1 = Notification(
            user_id=admin.id,
            title="High Value Approval Pending",
            message="Server Hardware purchase requires signature ($8500).",
            type="Approval_Request",
            is_read=False
        )
        audit_1 = AuditLog(
            organization_id=org.id,
            user_id=employee.id,
            workflow_id=wf_pending.id,
            action="Create_Workflow",
            entity_name="workflows",
            entity_id=wf_pending.id,
            payload={"title": wf_pending.title}
        )
        db.add(notif_1)
        db.add(audit_1)

        db.commit()
        StructuredLogger.info("Database sandbox seeder run completed successfully!")

    except Exception as e:
        db.rollback()
        StructuredLogger.error(f"Seeder script execution failed: rollback executed. Error: {str(e)}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
