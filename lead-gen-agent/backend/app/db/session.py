import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Try to get from env (Docker Compose sets this), fall back to .env
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:devpass@localhost:5432/leadgen"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()