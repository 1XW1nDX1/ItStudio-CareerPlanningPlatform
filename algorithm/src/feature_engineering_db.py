"""
大学生场景特征工程（增强版）
"""
import os
import re
import json
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_FEATURE_CSV = os.getenv("FEATURE_CSV_PATH", "./data/features_examples.csv")
_FEATURE_KEYWORDS_CACHE = None

def load_feature_keywords(csv_path=None):
    global _FEATURE_KEYWORDS_CACHE
    if _FEATURE_KEYWORDS_CACHE is not None:
        return _FEATURE_KEYWORDS_CACHE
    path = csv_path or DEFAULT_FEATURE_CSV
    if not os.path.exists(path):
        raise FileNotFoundError(f"特征关键词文件不存在：{path}")
    df = pd.read_csv(path, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    if "feature_name" not in df.columns or "keyword" not in df.columns:
        raise ValueError("features_examples.csv 必须包含 'feature_name' 和 'keyword' 两列。")
    result = {}
    for _, row in df.iterrows():
        fname = str(row["feature_name"]).strip()
        kw    = str(row["keyword"]).strip()
        result.setdefault(fname, []).append(kw)
    _FEATURE_KEYWORDS_CACHE = result
    return result

def reload_feature_keywords(csv_path=None):
    global _FEATURE_KEYWORDS_CACHE
    _FEATURE_KEYWORDS_CACHE = None
    return load_feature_keywords(csv_path)

def _contains_any(text, keywords):
    txt = str(text).lower()
    return int(any(k.lower() in txt for k in keywords))

def extract_skills_from_resume_text(resume_text, feature_keywords=None):
    if feature_keywords is None:
        feature_keywords = load_feature_keywords()
    skill_lexicon = feature_keywords.get("skill", [])
    text = str(resume_text).lower()
    return {kw.lower() for kw in skill_lexicon if kw.lower() in text}

def count_skill_matches(resume_skills, job_skill_tokens):
    job_skills = {str(s).lower() for s in job_skill_tokens}
    return len(resume_skills & job_skills)

def calc_skill_jaccard(resume_skills, job_skill_tokens):
    job_skills = {str(s).lower() for s in job_skill_tokens}
    union = resume_skills | job_skills
    if not union:
        return 0.0
    return len(resume_skills & job_skills) / len(union)

def calc_skill_coverage(resume_skills, job_skill_tokens):
    """岗位要求技能中，简历覆盖了多少比例（比 jaccard 更适合大学生）"""
    job_skills = {str(s).lower() for s in job_skill_tokens}
    if not job_skills:
        return 0.0
    return len(resume_skills & job_skills) / len(job_skills)

def calc_title_keyword_score(resume_text, job_title):
    """岗位标题关键词在简历中出现的比例"""
    if not job_title:
        return 0.0
    # 按中文词/英文词切分标题
    tokens = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', str(job_title).lower())
    if not tokens:
        return 0.0
    text = str(resume_text).lower()
    hit = sum(1 for t in tokens if t in text)
    return hit / len(tokens)

def calc_industry_match(resume_text, job_industry):
    """行业关键词粗匹配"""
    if not job_industry or str(job_industry) == "nan":
        return 0.0
    industry_tokens = re.findall(r'[\u4e00-\u9fa5]{2,}', str(job_industry))
    if not industry_tokens:
        return 0.0
    text = str(resume_text).lower()
    hit = sum(1 for t in industry_tokens if t in text)
    return min(hit / len(industry_tokens), 1.0)

def _job_full_text(row):
    return " ".join(filter(None, [
        getattr(row, "title", ""),
        getattr(row, "responsibility", ""),
        getattr(row, "work_content", ""),
        getattr(row, "job_requirement", ""),
    ]))

def build_features_from_db(
    resume_text,
    resume_vec,
    candidates_meta_rows,
    candidate_vecs,
    candidate_sims=None,
    feature_csv_path=None
):
    resume_text      = str(resume_text)
    feature_keywords = load_feature_keywords(feature_csv_path)
    resume_skills    = extract_skills_from_resume_text(resume_text, feature_keywords)

    has_internship             = _contains_any(resume_text, feature_keywords.get("has_internship", []))
    has_certificate            = _contains_any(resume_text, feature_keywords.get("has_certificate", []))
    has_project                = _contains_any(resume_text, feature_keywords.get("has_project", []))
    has_competition            = _contains_any(resume_text, feature_keywords.get("has_competition", []))
    has_learning_evidence      = _contains_any(resume_text, feature_keywords.get("has_learning_evidence", []))
    has_communication_evidence = _contains_any(resume_text, feature_keywords.get("has_communication_evidence", []))
    has_pressure_evidence      = _contains_any(resume_text, feature_keywords.get("has_pressure_evidence", []))

    feats = []
    for i, row in enumerate(candidates_meta_rows):
        job_skill_tokens = (
            json.loads(row.job_skill_tokens_json)
            if row.job_skill_tokens_json else []
        )

        if candidate_sims is not None:
            sim = float(candidate_sims[i])
        else:
            jvec = candidate_vecs[i:i + 1]
            sim  = float(cosine_similarity(resume_vec.reshape(1, -1), jvec)[0, 0])

        full_text = _job_full_text(row)

        feats.append({
            "job_uuid":      row.uuid,
            "sim":           sim,

            # 技能特征（新增 coverage）
            "skill_match":    count_skill_matches(resume_skills, job_skill_tokens),
            "skill_jaccard":  calc_skill_jaccard(resume_skills, job_skill_tokens),
            "skill_coverage": calc_skill_coverage(resume_skills, job_skill_tokens),

            # 标题 & 行业匹配（新增）
            "title_kw_score":  calc_title_keyword_score(resume_text, getattr(row, "title", "")),
            "industry_match":  calc_industry_match(resume_text, getattr(row, "industry", "")),

            # 大学生背景特征
            "has_internship":             has_internship,
            "has_certificate":            has_certificate,
            "has_project":                has_project,
            "has_competition":            has_competition,
            "has_learning_evidence":      has_learning_evidence,
            "has_communication_evidence": has_communication_evidence,
            "has_pressure_evidence":      has_pressure_evidence,

            # 岗位文本长度
            "job_title_len":     len(getattr(row, "title", "") or ""),
            "job_resp_len":      len(getattr(row, "responsibility", "") or ""),
            "job_content_len":   len(getattr(row, "work_content", "") or ""),
            "job_req_len":       len(getattr(row, "job_requirement", "") or ""),
            "job_full_text_len": len(full_text),
        })

    return pd.DataFrame(feats)