from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ContentTypeModel(Base):
    __tablename__ = 'content_type'
    
    id = Column(Integer, primary_key=True, index=True)
    content_name = Column(String(50), unique=True, index=True)
    icon = Column(String(50))

    # permissions = relationship("ContentPermission", back_populates="content_type")

    def __repr__(self):
        return f"<ContentType(id={self.id}, content_name='{self.content_name}, icon={self.icon}')>"
