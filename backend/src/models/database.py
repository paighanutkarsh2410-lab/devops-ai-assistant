from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://devops_user:devops_password_123@localhost:5432/devops_ai")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,          # Minimum connections
    max_overflow=15,      # Up to 20 total (5 + 15)
    pool_timeout=30,      # Wait 30s for connection
    pool_recycle=1800,    # Recycle connections every 30 min
    pool_pre_ping=True,   # Verify connections before use
    echo=False,
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
