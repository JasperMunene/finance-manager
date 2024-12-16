from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from finance_manager.models import Base

DATABASE_URL = "sqlite:///finance_manager.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()