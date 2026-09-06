"""Database sessions and SQLAlchemy metadata."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False, 'timeout': 30} if DATABASE_URL.startswith('sqlite') else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    with SessionLocal() as session:
        yield session
