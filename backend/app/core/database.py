from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
from app.core.logging import StructuredLogger

# Select connection parameters based on engine type
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # Lightweight local development mode supported via SQLite fallback
    connect_args = {"check_same_thread": False}
    StructuredLogger.warning("Running database in lightweight local development SQLite mode")
else:
    # Production-grade PostgreSQL pooling parameters
    connect_args = {
        # Custom keepalives and connection properties can go here if needed
    }
    StructuredLogger.info("Connecting to production PostgreSQL database pool")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Ensure database connection health checks on checkout
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db_context():
    """
    Generator yield logic to clean up open DB connections.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
