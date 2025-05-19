from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import String
from database.db import db

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
    country: Mapped[str]
    role: Mapped[str] = mapped_column(String, default="user")

    def __repr__(self) -> str:
        return f"User: {self.id}, email: {self.email}, role: {self.role}"
    
Base.metadata.create_all(bind=db)