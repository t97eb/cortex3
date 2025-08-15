import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_premium = Column(Boolean, default=False)
    remaining_requests = Column(Integer, default=10)
    remaining_files = Column(Integer, default=2)
    remaining_images = Column(Integer, default=1)
    premium_expiry = Column(DateTime)
    premium_code = Column(String)
    last_request_date = Column(String)
    join_date = Column(DateTime, default=datetime.utcnow)

class MessageLog(Base):
    __tablename__ = 'message_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    message_type = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PremiumCode(Base):
    __tablename__ = 'premium_codes'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    duration_days = Column(Integer)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer)
    used_at = Column(DateTime)

def init_db():
    engine = create_engine(os.getenv('DATABASE_URL'))
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

Session = init_db()
