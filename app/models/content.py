from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.main import Base

class ContentTypeModel(Base):
    __tablename__ = 'content_type'
    
    id = Column(Integer, primary_key=True, index=True)
    content_name = Column(String(50), unique=True, index=True)
    icon = Column(String(50))

    permissions = relationship("ContentPermissionModel", back_populates="content_type")

    def __repr__(self):
        return f"<ContentType(id={self.id}, content_name='{self.content_name}, icon={self.icon}')>"

class ContentPermissionModel(Base):
    __tablename__ = 'content_permission'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    content_type_id = Column(Integer, ForeignKey('content_type.id'))
    action = Column(String(10), nullable=False)
    
    content_type = relationship("ContentTypeModel", back_populates="permissions")
    user_permissions = relationship(
        "UserPermissionModel", 
        primaryjoin="ContentPermissionModel.id == UserPermissionModel.permission_id",
        back_populates="permission")
    
    def __repr__(self):
        return f"<ContentPermission(id={self.id}, name='{self.name}', content_type_id={self.content_type_id}, action={self.action})>"
