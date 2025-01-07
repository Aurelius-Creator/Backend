from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db.main import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    permissions = relationship("UserPermissionModel", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, is_superuser={self.is_superuser})>"


class UserPermissionModel(Base):
    __tablename__ = "users_permission"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    permission_id = Column(Integer, ForeignKey("content_permission.id"))
    active = Column(Integer)

    user = relationship("UserModel", back_populates="permissions")
    permission = relationship(
        "ContentPermissionModel",
        primaryjoin="UserPermissionModel.permission_id == ContentPermissionModel.id",
        back_populates="user_permissions",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "permission_id", name="user_permission_unique"),
    )

    def __repr__(self):
        return f"<UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id})>"
