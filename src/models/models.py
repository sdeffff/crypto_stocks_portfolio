from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import String, ForeignKey

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
    country: Mapped[str]
    role: Mapped[str] = mapped_column(String, default="user")
    pfp: Mapped[str]

    def __repr__(self) -> str:
        return f"User: {self.id}, email: {self.email}, role: {self.role}"

class Subscritions(Base):
    __tablename__ = "subscritions"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(ForeignKey("users.id"))
    crypto_name: Mapped[str]
    operator: Mapped[str]
    value: Mapped[int]
    currency: Mapped[str]
