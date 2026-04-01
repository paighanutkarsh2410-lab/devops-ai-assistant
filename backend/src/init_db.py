from models import Base, engine
from models.user import User
from models.incident import Incident
from models.metric import Metric
from models.alert import Alert


def init_database():
    """Create all tables in the database"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_database()
