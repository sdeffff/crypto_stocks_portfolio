import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from models import Base

load_dotenv()

db = create_engine(os.getenv('DB_CONN_LINE'))

Base.metadata.create_all(bind=db)

SessionLocal = sessionmaker(db)
session = SessionLocal()
