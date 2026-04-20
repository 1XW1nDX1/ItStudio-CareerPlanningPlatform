"""
把 jobs.csv 编码并写入 SQLite DB，主键用 UUID，可选导出 FAISS 索引。
CSV expected columns:
  job_id, title, company, address, salary, industry,
  responsibility, work_content, job_requirement, work_time,
  job_skill_tokens, min_years
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import argparse
import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import sessionmaker

from db_models import get_engine, create_tables, Job, make_uuid, job_row_from_dict

def normalize_skill_tokens(cell):
    if pd.isna(cell):
        return []
    if isinstance(cell, list):
        return cell
    s = str(cell).strip()
    if not s:
        return []
    try:
        val = json.loads(s)
        if isinstance(val, list):
            return [str(x).strip() for x in val if str(x).strip()]
    except Exception:
        pass
    return [tok.strip() for tok in s.split(",") if tok.strip()]

def build_job_input(row):
    """拼接向量化输入文本，优先用细分字段，兜底用 responsibility"""
    parts = [f"职位名称：{str(row.get('title', '')).strip()}"]

    for field, label in [
        ("work_content",    "工作内容"),
        ("job_requirement", "岗位要求"),
        ("responsibility",  "职责描述"),
    ]:
        val = str(row.get(field, "")).strip()
        if val:
            parts.append(f"{label}：{val}")

    skills = normalize_skill_tokens(row.get("job_skill_tokens", None))
    if skills:
        parts.append(f"技能要求：{'，'.join(skills)}")

    return "\n".join(parts)

def export_faiss_index(vectors: np.ndarray, save_path: str):
    import faiss
    vectors = vectors.astype("float32")
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    faiss.write_index(index, save_path)
    print(f"FAISS index saved to {save_path}")

def main(args):
    engine = get_engine(args.db_uri)
    create_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    jobs_df = pd.read_csv(args.jobs_csv)
    model   = SentenceTransformer(args.model_name_or_path)

    texts = [build_job_input(row) for _, row in jobs_df.iterrows()]
    vecs  = model.encode(
        texts,
        batch_size=args.batch_size,
        normalize_embeddings=True,
        show_progress_bar=True
    )
    vecs = np.array(vecs, dtype=np.float32)

    inserted = 0
    for idx, row in jobs_df.iterrows():
        vec = vecs[idx]

        job_id    = str(row["job_id"]) if "job_id" in jobs_df.columns and not pd.isna(row.get("job_id")) else None
        min_years = int(row["min_years"]) if "min_years" in jobs_df.columns and not pd.isna(row.get("min_years")) else None
        skills    = normalize_skill_tokens(row.get("job_skill_tokens", None))

        fields = job_row_from_dict({
            "title":           str(row.get("title", "")).strip(),
            "company":         str(row.get("company", "")).strip(),
            "address":         str(row.get("address", "")).strip(),
            "salary":          str(row.get("salary", "")).strip(),
            "industry":        str(row.get("industry", "")).strip(),
            "responsibility":  str(row.get("responsibility", "")).strip(),
            "work_content":    str(row.get("work_content", "")).strip(),
            "job_requirement": str(row.get("job_requirement", "")).strip(),
            "work_time":       str(row.get("work_time", "")).strip(),
            "job_skill_tokens": skills,
        })

        job = Job(
            uuid=make_uuid(),
            job_id=job_id,
            min_years=min_years,
            job_vector_json=json.dumps(vec.tolist(), ensure_ascii=False),
            **fields
        )
        session.add(job)
        inserted += 1

        if inserted % args.commit_every == 0:
            session.commit()

    session.commit()
    session.close()

    if args.faiss_index_path:
        export_faiss_index(vecs, args.faiss_index_path)

    print(f"Inserted {inserted} jobs into {args.db_uri}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--jobs_csv",             required=True)
    p.add_argument("--model_name_or_path",   default="paraphrase-multilingual-MiniLM-L12-v2")
    p.add_argument("--db_uri",               default="sqlite:///jobs.db")
    p.add_argument("--batch_size",           type=int, default=64)
    p.add_argument("--commit_every",         type=int, default=500)
    p.add_argument("--faiss_index_path",     default="./models/job_faiss.index")
    args = p.parse_args()
    main(args)