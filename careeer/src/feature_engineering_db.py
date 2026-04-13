"""
Feature builder that expects DB-fetched candidate_meta rows where JSON fields are strings.
All JSON fields are parsed with json.loads before usage.
"""
import json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def extract_skills_from_resume_text(resume_text):
    # TODO: replace with real NER/parser. Placeholder:
    toks = [t.strip().lower() for t in resume_text.replace('\n',' ').split() if len(t.strip())>2]
    return set(toks)

def count_skill_matches(resume_skills, job_skill_tokens):
    return len(resume_skills.intersection(set([s.lower() for s in job_skill_tokens])))

def extract_experience_years(text):
    import re
    m = re.search(r'(\d+)\s*(year|年)', text)
    return int(m.group(1)) if m else 0

def build_features_from_db(resume_text, resume_vec, candidates_meta_rows, candidate_vecs):
    """
    candidates_meta_rows: list of SQLAlchemy Job rows (or dicts) with job_*_json fields as JSON strings
    candidate_vecs: np.array aligned with candidates_meta_rows
    Returns DataFrame with job_uuid and features (all basic examples)
    """
    resume_skills = extract_skills_from_resume_text(resume_text)
    resume_years = extract_experience_years(resume_text)

    feats = []
    for i, row in enumerate(candidates_meta_rows):
        # parse JSONs
        job_text_obj = json.loads(row.job_text_json)
        job_skill_tokens = json.loads(row.job_skill_tokens_json) if row.job_skill_tokens_json else []
        min_years = int(row.min_years) if row.min_years is not None else 0

        jvec = candidate_vecs[i:i+1]
        sim = float(cosine_similarity(resume_vec.reshape(1, -1), jvec)[0,0])
        skill_match = count_skill_matches(resume_skills, job_skill_tokens)
        years_diff = max(0, (min_years - resume_years))

        feats.append({
            'job_uuid': row.uuid,
            'sim': sim,
            'skill_match': skill_match,
            'years_diff': years_diff
        })
    return pd.DataFrame(feats)