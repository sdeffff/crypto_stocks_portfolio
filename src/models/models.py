from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import String, ForeignKey, Boolean

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
    country: Mapped[str]
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="user")
    pfp: Mapped[str]
    premium: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"User: {self.id}, email: {self.email}, role: {self.role}"


class Subscritions(Base):
    __tablename__ = "subscritions"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(ForeignKey("users.id"))
    check_type: Mapped[str]
    what_to_check: Mapped[str]
    operator: Mapped[str]
    value: Mapped[int]
    currency: Mapped[str]


class Notifications(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(ForeignKey("users.id"))
    check_type: Mapped[str]
    what_to_check: Mapped[str]
    operator: Mapped[str]
    value: Mapped[int]
    currency: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.now(),
        nullable=False
    )


class Verifications(Base):
    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    code: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.now(),
        nullable=False
    )
