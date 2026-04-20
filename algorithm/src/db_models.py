"""
数据库模型：使用 SQLite + SQLAlchemy。
所有复杂字段以 JSON 字符串存储（Text）。
主键使用 UUID 字符串（version4）。
"""
import uuid
import json
from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    uuid                  = Column(String(36), primary_key=True)
    job_id                = Column(String(128), index=True, nullable=True)
    title                 = Column(Text, nullable=True)
    company               = Column(Text, nullable=True)
    address               = Column(Text, nullable=True)
    salary                = Column(Text, nullable=True)
    industry              = Column(Text, nullable=True)
    responsibility        = Column(Text, nullable=True)
    work_content          = Column(Text, nullable=True)
    job_requirement       = Column(Text, nullable=True)
    work_time             = Column(Text, nullable=True)
    job_skill_tokens_json = Column(Text, nullable=True)
    min_years             = Column(Integer, index=True, nullable=True)
    job_vector_json       = Column(Text, nullable=True)

def get_engine(db_uri="sqlite:///jobs.db"):
    return create_engine(db_uri, connect_args={"check_same_thread": False})

def create_tables(engine):
    Base.metadata.create_all(engine)

def make_uuid():
    return str(uuid.uuid4())

def job_row_from_dict(dct):
    return {
        "title":                 dct.get("title", ""),
        "company":               dct.get("company", ""),
        "address":               dct.get("address", ""),
        "salary":                dct.get("salary", ""),
        "industry":              dct.get("industry", ""),
        "responsibility":        dct.get("responsibility", ""),
        "work_content":          dct.get("work_content", ""),
        "job_requirement":       dct.get("job_requirement", ""),
        "work_time":             dct.get("work_time", ""),
        "job_skill_tokens_json": json.dumps(dct.get("job_skill_tokens", []), ensure_ascii=False),
    }

if __name__ == "__main__":
    engine = get_engine()
    create_tables(engine)
    print("Created tables at jobs.db")