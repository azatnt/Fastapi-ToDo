from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    items = relationship("Item", back_populates="user")


class Item(Base):
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    description = Column(Text)
    user_id = Column(ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="items")
