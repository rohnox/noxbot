from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.settings import Settings

settings = Settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
