import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

load_dotenv()

db = create_engine(os.getenv('DB_CONN_LINE'))

SessionLocal = sessionmaker(db)
session = SessionLocal()
