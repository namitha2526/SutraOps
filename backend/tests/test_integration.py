import os
import sys
import unittest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

# Set environment variable to use test SQLite database before imports
os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

# Insert workspace path
sys.path.append("backend")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db_context
from app.core.deps import get_db
from app.core.security import get_password_hash, create_access_token
from app.models.tenant import Organization, Department
from app.models.user import User
from app.models.workflow import Workflow, WorkflowStep
from app.models.approval import Approval, Task


# Define test database setup
TEST_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency override to use the testing session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestNexusFlowIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create database and all tables
        Base.metadata.create_all(bind=engine)
        cls.db = TestingSessionLocal()

        # Seed Tenant A
        cls.org_a = Organization(id=uuid4(), name="Tenant A Corp", domain="tenanta.com", is_active=True)
        cls.db.add(cls.org_a)
        cls.db.flush()

        cls.dept_a = Department(id=uuid4(), organization_id=cls.org_a.id, name="IT", code="IT")
        cls.db.add(cls.dept_a)
        cls.db.flush()

        # Users for Tenant A
        pw_hash = get_password_hash("password123")
        cls.user_a_admin = User(
            id=uuid4(),
            organization_id=cls.org_a.id,
            department_id=cls.dept_a.id,
            email="admin@tenanta.com",
            hashed_password=pw_hash,
            full_name="Admin A",
            role="Admin",
            is_active=True
        )
        cls.user_a_employee = User(
            id=uuid4(),
            organization_id=cls.org_a.id,
            department_id=cls.dept_a.id,
            email="employee@tenanta.com",
            hashed_password=pw_hash,
            full_name="Employee A",
            role="Employee",
            is_active=True
        )
        cls.db.add(cls.user_a_admin)
        cls.db.add(cls.user_a_employee)

        # Seed Tenant B
        cls.org_b = Organization(id=uuid4(), name="Tenant B Corp", domain="tenantb.com", is_active=True)
        cls.db.add(cls.org_b)
        cls.db.flush()

        cls.user_b_admin = User(
            id=uuid4(),
            organization_id=cls.org_b.id,
            email="admin@tenantb.com",
            hashed_password=pw_hash,
            full_name="Admin B",
            role="Admin",
            is_active=True
        )
        cls.db.add(cls.user_b_admin)
        cls.db.commit()

        # Generate tokens
        cls.token_a_admin = create_access_token(cls.user_a_admin.id, cls.org_a.id, cls.user_a_admin.role)
        cls.token_a_employee = create_access_token(cls.user_a_employee.id, cls.org_a.id, cls.user_a_employee.role)
        cls.token_b_admin = create_access_token(cls.user_b_admin.id, cls.org_b.id, cls.user_b_admin.role)

        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        # Dispose engine connections pool to unlock file handle on Windows
        engine.dispose()
        from app.core.database import engine as app_engine
        app_engine.dispose()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("test_temp.db"):
            try:
                os.remove("test_temp.db")
            except PermissionError:
                pass

    def test_tenant_isolation(self):
        # 1. Tenant A employee creates a workflow
        headers_a = {"Authorization": f"Bearer {self.token_a_employee}"}
        payload = {
            "title": "Tenant A Workstation Purchase",
            "description": "Purchase software developer laptops",
            "context_data": {"amount": 2500, "department_code": "IT"},
            "steps": [
                {
                    "name": "Manager Approval",
                    "step_order": 1,
                    "approver_role": "Admin"
                }
            ]
        }
        res = self.client.post("/api/v1/workflows", json=payload, headers=headers_a)
        self.assertEqual(res.status_code, 201)
        wf_id = res.json()["id"]

        # 2. Verify Tenant A admin can fetch this workflow
        res_fetch_a = self.client.get(f"/api/v1/workflows/{wf_id}", headers={"Authorization": f"Bearer {self.token_a_admin}"})
        self.assertEqual(res_fetch_a.status_code, 200)
        self.assertEqual(res_fetch_a.json()["title"], "Tenant A Workstation Purchase")

        # 3. Verify Tenant B admin CANNOT fetch this workflow (should return 404 due to tenant query filter)
        res_fetch_b = self.client.get(f"/api/v1/workflows/{wf_id}", headers={"Authorization": f"Bearer {self.token_b_admin}"})
        self.assertEqual(res_fetch_b.status_code, 404)

    def test_rbac_constraints(self):
        # Employee should be forbidden from accessing analytics (403)
        res = self.client.get("/api/v1/analytics", headers={"Authorization": f"Bearer {self.token_a_employee}"})
        self.assertEqual(res.status_code, 403)

        # Admin should be allowed to access analytics
        res_admin = self.client.get("/api/v1/analytics", headers={"Authorization": f"Bearer {self.token_a_admin}"})
        self.assertEqual(res_admin.status_code, 200)

    def test_idempotency_protection(self):
        headers = {
            "Authorization": f"Bearer {self.token_a_employee}",
            "Idempotency-Key": f"test-idemp-key-{uuid4()}"
        }
        payload = {
            "title": "Idempotent Request Test",
            "description": "Should only write once",
            "steps": [{"name": "Step 1", "step_order": 1, "approver_role": "Admin"}]
        }
        
        # First request succeeds
        res1 = self.client.post("/api/v1/workflows", json=payload, headers=headers)
        self.assertEqual(res1.status_code, 201)
        wf_id1 = res1.json()["id"]

        # Second request returns the cached response instead of creating another workflow
        res2 = self.client.post("/api/v1/workflows", json=payload, headers=headers)
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(res2.json()["id"], wf_id1)

    def test_double_approval_concurrency_control(self):
        # Create a workflow and start processing it
        headers_a = {"Authorization": f"Bearer {self.token_a_employee}"}
        payload = {
            "title": "Concurrency Test Workflow",
            "description": "Double signoff verify",
            "steps": [{"name": "Signoff Step", "step_order": 1, "approver_role": "Admin"}]
        }
        res_wf = self.client.post("/api/v1/workflows", json=payload, headers=headers_a)
        wf_id = res_wf.json()["id"]

        # Start it
        res_start = self.client.post(f"/api/v1/workflows/{wf_id}/start", json={}, headers=headers_a)
        self.assertEqual(res_start.status_code, 200)

        # Fetch the pending approval ID
        db_session = TestingSessionLocal()
        approval_record = db_session.query(Approval).filter(
            Approval.workflow_id == UUID(wf_id),
            Approval.status == "Pending"
        ).first()
        self.assertIsNotNone(approval_record)
        app_id = str(approval_record.id)
        db_session.close()

        # Simulate two concurrent sessions fetching the same approval record and actioning it
        db_sess1 = TestingSessionLocal()
        db_sess2 = TestingSessionLocal()

        app_rec1 = db_sess1.query(Approval).filter(Approval.id == approval_record.id).first()
        app_rec2 = db_sess2.query(Approval).filter(Approval.id == approval_record.id).first()

        # Session 1 updates approval status and commits
        app_rec1.status = "Approved"
        app_rec1.actioned_at = datetime.utcnow()
        db_sess1.commit()

        # Session 2 attempts to update the SAME record status and commit
        app_rec2.status = "Rejected"
        app_rec2.actioned_at = datetime.utcnow()

        # In SQLAlchemy, committing this will trigger StaleDataError because the version_id of the row is now 2,
        # but the instance session 2 held has version_id=1.
        with self.assertRaises(Exception):
            db_sess2.commit()

        db_sess1.close()
        db_sess2.close()


if __name__ == "__main__":
    unittest.main()
