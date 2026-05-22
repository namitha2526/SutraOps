from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.tenant import Department
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Retrieves a user by email across all tenants (needed during initial login handshake).
        """
        return db.query(self.model).filter(self.model.email == email).first()

    def get_users_by_role(self, db: Session, role: str) -> list[User]:
        """
        Fetches all users matching a role index inside current tenant scope.
        """
        query = db.query(self.model).filter(self.model.role == role)
        query = self._apply_tenant_filter(query, db)
        return query.all()


class DepartmentRepository(BaseRepository[Department]):
    def get_by_code(self, db: Session, code: str) -> Optional[Department]:
        """
        Resolves a department by organizational code inside current tenant scope.
        """
        query = db.query(self.model).filter(self.model.code == code)
        query = self._apply_tenant_filter(query, db)
        return query.first()


user_repo = UserRepository(User)
department_repo = DepartmentRepository(Department)
