import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

environment = os.getenv('ENVIRONMENT', 'development')
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'environments', f".env-{environment}")
load_dotenv(env_file)
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL_LOCAL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()