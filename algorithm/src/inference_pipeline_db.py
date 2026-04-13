"""
End-to-end inference using DB-stored UUIDs & JSON fields.

从 DB 读取所有 job rows（或部分），把 job_vector_json 转为 ndarray
对 resume 编码 -> 在内存中计算余弦相似度召回 top_k
使用 feature_engineering_db 构建 features
使用 LightGBM 模型做 re-rank（如果已训练并保存）

"""

import argparse
import numpy as np
import joblib
import json
from sqlalchemy.orm import sessionmaker
from db_models import get_engine, Job
from sentence_transformers import SentenceTransformer
from feature_engineering_db import build_features_from_db
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

def load_all_jobs_from_db(db_uri):
    engine = get_engine(db_uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    rows = session.query(Job).all()
    session.close()
    return rows

def rows_to_vectors(rows):
    vecs = []
    for r in rows:
        if r.job_vector_json:
            arr = np.array(json.loads(r.job_vector_json), dtype=float)
        else:
            arr = np.zeros((768,), dtype=float)  # fallback dim; but ideally always present
        vecs.append(arr)
    return np.vstack(vecs)

def topk_by_cosine_in_memory(resume_vec, job_vectors, topk=100):
    sims = cosine_similarity(resume_vec.reshape(1, -1), job_vectors)[0]
    idx = np.argsort(-sims)[:topk]
    return idx, sims[idx]

def load_lgb_model(path):
    obj = joblib.load(path)
    return obj['model'], obj['features']

def main(args):
    # load model & DB
    model = SentenceTransformer(args.model_path)
    rows = load_all_jobs_from_db(args.db_uri)
    job_vectors = rows_to_vectors(rows)  # shape (N, dim)

    # encode resume
    resume_vec = model.encode([args.resume_text], normalize_embeddings=True)[0]

    idxs, sims = topk_by_cosine_in_memory(resume_vec, job_vectors, topk=args.recall_k)
    candidate_rows = [rows[i] for i in idxs]
    candidate_vecs = job_vectors[idxs]

    # build features
    feats_df = build_features_from_db(args.resume_text, resume_vec, candidate_rows, candidate_vecs)

    # load LGB model if provided
    if args.lgb_model:
        lgb_model, feature_list = load_lgb_model(args.lgb_model)
        X = feats_df[feature_list].fillna(0)
        scores = lgb_model.predict(X)
        feats_df['lgb_score'] = scores
        feats_df = feats_df.sort_values('lgb_score', ascending=False)
    else:
        feats_df = feats_df.sort_values('sim', ascending=False)

    # join with metadata for output
    out_rows = []
    for _, r in feats_df.head(20).iterrows():
        job_uuid = r['job_uuid']
        row_meta = next(filter(lambda x: x.uuid == job_uuid, candidate_rows))
        job_text = json.loads(row_meta.job_text_json).get('text', '')
        out_rows.append({
            'uuid': job_uuid,
            'job_text': job_text,
            'sim': float(r.get('sim', 0)),
            'lgb_score': float(r.get('lgb_score', 0)) if 'lgb_score' in r else None
        })
    print(json.dumps(out_rows, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model_path", required=True)
    p.add_argument("--db_uri", default="sqlite:///jobs.db")
    p.add_argument("--resume_text", required=True)
    p.add_argument("--recall_k", type=int, default=100)
    p.add_argument("--lgb_model", default=None)
    args = p.parse_args()
    main(args)