from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from app.core.database import Base
from app.core.logging import organization_id_ctx, StructuredLogger

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        Base Repository pattern mapping db entities.
        """
        self.model = model

    def _get_tenant_id(self) -> Optional[str]:
        """
        Retrieves current tenant ID from context safely.
        """
        org_id = organization_id_ctx.get()
        return org_id if org_id else None

    def _apply_tenant_filter(self, query, session: Session):
        """
        Inspects model fields, dynamically appending organization isolation constraints.
        """
        tenant_id = self._get_tenant_id()
        if hasattr(self.model, "organization_id") and tenant_id:
            return query.filter(self.model.organization_id == tenant_id)
        return query

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        query = db.query(self.model).filter(self.model.id == id)
        query = self._apply_tenant_filter(query, db)
        return query.first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        query = db.query(self.model)
        query = self._apply_tenant_filter(query, db)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        # Check if model has organization_id and populate it automatically if missing in payload
        tenant_id = self._get_tenant_id()
        if hasattr(self.model, "organization_id") and "organization_id" not in obj_in and tenant_id:
            obj_in["organization_id"] = tenant_id

        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], Any]
    ) -> ModelType:
        # Enforce tenant check before updating to ensure no cross-tenant mutation is possible
        tenant_id = self._get_tenant_id()
        if hasattr(self.model, "organization_id") and tenant_id:
            obj_org_id = getattr(db_obj, "organization_id", None)
            if obj_org_id and str(obj_org_id) != str(tenant_id):
                StructuredLogger.error(
                    f"Tenant breach attempt: Blocked cross-tenant update on {self.model.__tablename__}",
                    obj_id=str(db_obj.id),
                    attempted_tenant=tenant_id,
                    object_tenant=str(obj_org_id)
                )
                raise PermissionError("Access Denied: Tenant boundary breach blocked")

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.__dict__

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType:
        obj = self.get(db, id)
        if not obj:
            raise ValueError("Target record not found")

        # Enforce tenant check before deletion
        tenant_id = self._get_tenant_id()
        if hasattr(self.model, "organization_id") and tenant_id:
            obj_org_id = getattr(obj, "organization_id", None)
            if obj_org_id and str(obj_org_id) != str(tenant_id):
                StructuredLogger.error(
                    f"Tenant breach attempt: Blocked cross-tenant deletion on {self.model.__tablename__}",
                    obj_id=str(id),
                    attempted_tenant=tenant_id,
                    object_tenant=str(obj_org_id)
                )
                raise PermissionError("Access Denied: Tenant boundary breach blocked")

        db.delete(obj)
        db.commit()
        return obj
