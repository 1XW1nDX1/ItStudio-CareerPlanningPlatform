"""
数据库模型：使用 SQLite + SQLAlchemy。
所有可读字段以 JSON 字符串存储（Text）。
主键使用 UUID 字符串（version4）。
"""
import uuid
import json
from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    uuid = Column(String(36), primary_key=True)  # UUID v4 string
    job_id = Column(String(128), nullable=True)  # 原始 job_id 可选保存
    job_text_json = Column(Text, nullable=False)  # JSON string: {"text": "..."}
    job_skill_tokens_json = Column(Text, nullable=True)  # JSON string: ["skill1","skill2"]
    min_years = Column(Integer, nullable=True)
    job_vector_json = Column(Text, nullable=True)  # JSON string: [0.123, 0.456, ...]
    extra_json = Column(Text, nullable=True)  # 其他结构化信息以 JSON 存储

def get_engine(db_path="sqlite:///jobs.db"):
    return create_engine(db_path, connect_args={"check_same_thread": False})

def create_tables(engine):
    Base.metadata.create_all(engine)

def make_uuid():
    return str(uuid.uuid4())

def job_row_from_dict(dct):
    """Helper to produce JSON strings for fields, ensure all stored as JSON strings."""
    return {
        "job_text_json": json.dumps({"text": dct.get("job_text", "")}, ensure_ascii=False),
        "job_skill_tokens_json": json.dumps(dct.get("job_skill_tokens", []), ensure_ascii=False),
        "extra_json": json.dumps(dct.get("extra", {}), ensure_ascii=False)
    }

if __name__ == "__main__":
    engine = get_engine()
    create_tables(engine)
    print("Created tables at jobs.db")