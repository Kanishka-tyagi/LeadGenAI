"""
Initialize the database — create tables and seed data.
Run this once on startup.
"""
from app.db.models import LeadModel, JobModel
from app.db.session import Base, engine
from app.db.seed import seed

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    # Seed data
    seed()
    print("✓ Data seeded")

if __name__ == "__main__":
    init_db()