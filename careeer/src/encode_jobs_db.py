"""
把 jobs.csv 编码并写入 SQLite DB，字段都以 JSON 字符串形式保存，主键用 UUID。
CSV expected columns: job_id (optional), job_text, job_skill_tokens (optional as json-list-string), min_years (optional)
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
    # If the CSV cell already contains a json list string, try to parse
    if pd.isna(cell):
        return []
    if isinstance(cell, list):
        return cell
    s = str(cell).strip()
    try:
        val = json.loads(s)
        if isinstance(val, list):
            return val
    except Exception:
        pass
    # fallback: split by comma
    return [tok.strip() for tok in s.split(",") if tok.strip()]

def main(args):
    engine = get_engine(args.db_uri)
    create_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    import os
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

    from huggingface_hub import snapshot_download
    snapshot_download(
        repo_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        local_dir="./model",
        
    )
    model = SentenceTransformer("./model")

   
    jobs_df = pd.read_csv(args.jobs_csv)
    for idx, row in jobs_df.iterrows():
        job_id = str(row.get('job_id')) if 'job_id' in row and not pd.isna(row['job_id']) else None
        job_text = str(row.get('job_text', ''))
        skill_tokens = normalize_skill_tokens(row.get('job_skill_tokens', None))
        min_years = int(row['min_years']) if 'min_years' in row and not pd.isna(row['min_years']) else None

        # encode vector
        vec = model.encode([job_text], normalize_embeddings=True)[0]
        vec_list = vec.tolist()

        # build Job row
        uuid = make_uuid()
        job_json_fields = job_row_from_dict({
            "job_text": job_text,
            "job_skill_tokens": skill_tokens,
            "extra": {"source_row_index": int(idx)}
        })

        job = Job(
            uuid=uuid,
            job_id=job_id,
            job_text_json=job_json_fields["job_text_json"],
            job_skill_tokens_json=job_json_fields["job_skill_tokens_json"],
            min_years=min_years,
            job_vector_json=json.dumps(vec_list, ensure_ascii=False),
            extra_json=job_json_fields["extra_json"]
        )
        session.add(job)
    session.commit()
    session.close()
    print(f"Inserted {len(jobs_df)} jobs into DB at {args.db_uri}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--jobs_csv", required=True)
    p.add_argument("--model_name", default="paraphrase-multilingual-MiniLM-L12-v2")
    p.add_argument("--db_uri", default="sqlite:///jobs.db")
    args = p.parse_args()
    main(args)