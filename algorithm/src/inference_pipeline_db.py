import argparse
import json
import os
import re
import numpy as np
import joblib

from sqlalchemy.orm import sessionmaker
from db_models import get_engine, Job
from sentence_transformers import SentenceTransformer
from feature_engineering_db import (
    build_features_from_db,
    extract_skills_from_resume_text,
)
from sklearn.metrics.pairwise import cosine_similarity

# ── 简历扩写 ──────────────────────────────────────────────────────────────────
def expand_resume_text(resume_text: str) -> str:
    return (
        "求职者简历信息如下：\n"
        f"{resume_text.strip()}\n"
        "求职意向：寻找与以上技能和经历匹配的岗位。"
    )

class RecommendationEngine:
    def __init__(self, model_path, db_uri, lgb_model_path=None, faiss_index_path=None):
        self.model_path       = model_path
        self.db_uri           = db_uri
        self.lgb_model_path   = lgb_model_path
        self.faiss_index_path = faiss_index_path

        self.model         = None
        self.rows          = []
        self.job_vectors   = None
        self.row_map       = {}
        self.uuid_to_index = {}
        self.lgb_model     = None
        self.feature_list  = None
        self.faiss_index   = None
        self.use_lgb       = False  # ← 关键标志位

    def load(self):
        self._load_model()
        self._load_jobs()
        self._load_lgb_model()
        self._load_faiss_index()

    def _load_model(self):
        print(f"[Info] 加载 BERT 模型: {self.model_path}")
        self.model = SentenceTransformer(self.model_path)
        print(f"[Info] ✅ BERT 模型加载成功")

    def _load_jobs(self):
        engine  = get_engine(self.db_uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        self.rows = session.query(Job).all()
        session.close()

        if not self.rows:
            raise ValueError("No jobs found in DB.")

        dim  = self.model.get_sentence_embedding_dimension()
        vecs = []
        for idx, r in enumerate(self.rows):
            vec = (
                np.array(json.loads(r.job_vector_json), dtype=np.float32)
                if r.job_vector_json
                else np.zeros((dim,), dtype=np.float32)
            )
            vecs.append(vec)
            self.row_map[r.uuid]       = r
            self.uuid_to_index[r.uuid] = idx

        self.job_vectors = np.vstack(vecs).astype(np.float32)
        print(f"[Info] ✅ 加载 {len(self.rows)} 个岗位")

    def _load_lgb_model(self):
        """✅ 修正后的 LightGBM 加载逻辑"""
        if not self.lgb_model_path:
            print("[Warn] lgb_model_path 未设置，跳过 LightGBM 加载")
            self.use_lgb = False
            return

        print(f"[Info] 尝试加载 LightGBM 模型: {self.lgb_model_path}")
        
        if not os.path.exists(self.lgb_model_path):
            print(f"[Error] ❌ 模型文件不存在: {self.lgb_model_path}")
            print(f"[Debug] 当前工作目录: {os.getcwd()}")
            print(f"[Debug] 绝对路径: {os.path.abspath(self.lgb_model_path)}")
            self.use_lgb = False
            return

        try:
            obj = joblib.load(self.lgb_model_path)
            print(f"[Debug] 加载成功，类型: {type(obj)}")
            
            if isinstance(obj, dict):
                print(f"[Debug] 字典键: {list(obj.keys())}")
                
                # 兼容 "model" 或 "lgb_model"
                if "model" in obj:
                    self.lgb_model = obj["model"]
                elif "lgb_model" in obj:
                    self.lgb_model = obj["lgb_model"]
                else:
                    raise ValueError(f"模型字典中找不到 'model' 或 'lgb_model' 键，实际键: {list(obj.keys())}")
                
                # 兼容 "features" 或 "feature_names"
                if "features" in obj:
                    self.feature_list = obj["features"]
                elif "feature_names" in obj:
                    self.feature_list = obj["feature_names"]
                else:
                    raise ValueError(f"模型字典中找不到 'features' 或 'feature_names' 键，实际键: {list(obj.keys())}")
                
                print(f"[Info] ✅ LightGBM 模型加载成功")
                print(f"[Info] 特征数量: {len(self.feature_list)}")
                print(f"[Info] 特征列表: {self.feature_list}")
                self.use_lgb = True
                
            else:
                # 如果是纯模型对象
                self.lgb_model = obj
                if hasattr(obj, "feature_name_"):
                    self.feature_list = list(obj.feature_name_)
                elif hasattr(obj, "feature_name"):
                    self.feature_list = obj.feature_name()
                else:
                    raise ValueError("无法从模型对象中提取特征列表")
                
                print(f"[Info] ✅ LightGBM 模型加载成功（纯对象模式）")
                print(f"[Info] 特征数量: {len(self.feature_list)}")
                self.use_lgb = True
                
        except Exception as e:
            print(f"[Error] ❌ LightGBM 加载失败: {e}")
            import traceback
            traceback.print_exc()
            self.use_lgb = False

    def _load_faiss_index(self):
        if self.faiss_index_path and os.path.exists(self.faiss_index_path):
            import faiss
            self.faiss_index = faiss.read_index(self.faiss_index_path)
            print(f"[Info] ✅ FAISS 索引加载成功")

    # ── 向量召回 ──────────────────────────────────────────────────────────
    def _vec_recall(self, query_vec: np.ndarray, topk: int):
        query_vec = query_vec.astype(np.float32).reshape(1, -1)
        if self.faiss_index is not None:
            scores, indices = self.faiss_index.search(query_vec, topk)
            valid = [(i, s) for i, s in zip(indices[0], scores[0]) if i >= 0]
            if not valid:
                return np.array([], dtype=int), np.array([], dtype=float)
            return (
                np.array([x[0] for x in valid], dtype=int),
                np.array([x[1] for x in valid], dtype=float),
            )
        sims = cosine_similarity(query_vec, self.job_vectors)[0]
        idx  = np.argsort(-sims)[:topk]
        return idx, sims[idx]

    def recall(self, resume_text: str, resume_vec: np.ndarray, topk: int = 100):
        """双路召回"""
        idxs1, sims1 = self._vec_recall(resume_vec, topk)

        expanded_vec = self.model.encode(
            [expand_resume_text(resume_text)],
            normalize_embeddings=True
        )[0].astype(np.float32)
        idxs2, sims2 = self._vec_recall(expanded_vec, topk)

        # 合并去重
        merged = {}
        for i, s in zip(idxs1, sims1):
            merged[int(i)] = max(merged.get(int(i), -1), float(s))
        for i, s in zip(idxs2, sims2):
            merged[int(i)] = max(merged.get(int(i), -1), float(s))

        sorted_items = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:topk]
        idxs = np.array([x[0] for x in sorted_items], dtype=int)
        sims = np.array([x[1] for x in sorted_items], dtype=float)
        return idxs, sims

    # ── 精排 ──────────────────────────────────────────────────────────────
    def rerank(self, resume_text, resume_vec, candidate_rows, candidate_vecs, candidate_sims=None):
        """✅ 修正后的精排逻辑"""
        feats_df = build_features_from_db(
            resume_text=resume_text,
            resume_vec=resume_vec,
            candidates_meta_rows=candidate_rows,
            candidate_vecs=candidate_vecs,
            candidate_sims=candidate_sims
        )

        # ✅ 关键：判断是否使用 LightGBM
        if self.use_lgb and self.lgb_model is not None and self.feature_list is not None:
            print(f"[Rerank] 使用 LightGBM 精排，候选数: {len(feats_df)}")
            
            # 确保所有特征都存在
            for col in self.feature_list:
                if col not in feats_df.columns:
                    print(f"[Warn] 特征 '{col}' 不存在，填充为 0")
                    feats_df[col] = 0
            
            X = feats_df[self.feature_list].fillna(0)
            
            # ✅ 预测
            scores = self.lgb_model.predict(X)
            feats_df["rank_score"] = scores
            
            print(f"[Rerank] LightGBM 预测完成")
            print(f"[Rerank] 分数范围: [{scores.min():.4f}, {scores.max():.4f}]")
            print(f"[Rerank] 分数均值: {scores.mean():.4f}")
            
        else:
            print(f"[Rerank] 使用默认加权公式（LightGBM 未启用）")
            # 默认加权公式
            feats_df["rank_score"] = (
                feats_df["sim"]            * 0.45 +
                feats_df["skill_coverage"] * 0.25 +
                feats_df["title_kw_score"] * 0.15 +
                feats_df["industry_match"] * 0.05 +
                (feats_df["skill_match"] > 0).astype(float) * 0.04 +
                feats_df.get("has_project",     0) * 0.03 +
                feats_df.get("has_internship",  0) * 0.02 +
                feats_df.get("has_certificate", 0) * 0.01
            )

        return feats_df.sort_values("rank_score", ascending=False)

    # ── 解释生成（✨ 优化版）──────────────────────────────────────────────
    def _build_explanation(self, resume_text, row_meta, feat_row):
        """生成个性化的推荐解释"""
        resume_skills  = extract_skills_from_resume_text(resume_text)
        job_skills     = json.loads(row_meta.job_skill_tokens_json) if row_meta.job_skill_tokens_json else []
        job_skill_set  = {str(s).lower() for s in job_skills}
        matched_skills = list(resume_skills & job_skill_set)[:5]
        missing_skills = list(job_skill_set - resume_skills)[:5]

        # 提取特征值
        sim              = float(feat_row.get("sim", 0))
        skill_match      = int(feat_row.get("skill_match", 0))
        skill_coverage   = float(feat_row.get("skill_coverage", 0))
        title_kw         = float(feat_row.get("title_kw_score", 0))
        industry_match   = float(feat_row.get("industry_match", 0))
        has_project      = int(feat_row.get("has_project", 0))
        has_internship   = int(feat_row.get("has_internship", 0))
        has_certificate  = int(feat_row.get("has_certificate", 0))
        has_competition  = int(feat_row.get("has_competition", 0))
        has_learning     = int(feat_row.get("has_learning_evidence", 0))
        has_communication = int(feat_row.get("has_communication_evidence", 0))
        has_pressure     = int(feat_row.get("has_pressure_evidence", 0))

        # ── 1. 匹配原因 ──────────────────────────────────────────────
        reasons = []
        if sim > 0.65:       reasons.append("简历与岗位语义高度匹配")
        elif sim > 0.50:     reasons.append("简历与岗位语义相似度较高")
        elif sim > 0.40:     reasons.append("简历与岗位具备一定语义相关性")
        if skill_match > 0:  reasons.append(f"匹配到 {skill_match} 个岗位技能关键词")
        if skill_coverage > 0.5: reasons.append(f"覆盖岗位 {skill_coverage:.0%} 的技能要求")
        if title_kw > 0.5:   reasons.append("简历内容与岗位名称高度相关")
        if industry_match > 0: reasons.append("行业背景与岗位匹配")
        if has_project:      reasons.append("简历中包含项目经历")
        if has_internship:   reasons.append("简历中包含实习经历")
        if has_certificate:  reasons.append("简历中包含证书/认证信息")
        if has_competition:  reasons.append("简历中包含竞赛或创新经历")

        # ── 2. 优势分析（✨ 个性化）────────────────────────────────────
        strengths = []
        
        # 技能优势（根据匹配技能具体说明）
        if matched_skills:
            if skill_coverage >= 0.7:
                strengths.append(f"掌握岗位核心技能：{', '.join(matched_skills[:3])}，技能覆盖度达 {skill_coverage:.0%}")
            elif skill_coverage >= 0.5:
                strengths.append(f"具备岗位关键技能：{', '.join(matched_skills[:3])}，覆盖 {skill_coverage:.0%} 的技能要求")
            elif len(matched_skills) >= 2:
                strengths.append(f"掌握部分岗位技能：{', '.join(matched_skills[:2])}，具备一定技术基础")
            else:
                strengths.append(f"具备 {matched_skills[0]} 技能基础")
        
        # 项目经验优势
        if has_project:
            if skill_match >= 3:
                strengths.append("项目经历与岗位技术栈高度匹配，具备实战经验")
            elif skill_match >= 1:
                strengths.append("有相关项目实践经验，能快速上手岗位工作")
            else:
                strengths.append("具备项目开发经验，有一定工程实践能力")
        
        # 实习经验优势
        if has_internship:
            if industry_match > 0:
                strengths.append("有相关行业实习经历，熟悉业务场景和工作流程")
            elif title_kw > 0.5:
                strengths.append("有相关岗位实习经验，了解岗位职责和工作内容")
            else:
                strengths.append("有实习经历，具备一定职场适应能力")
        
        # 证书/认证优势
        if has_certificate:
            if skill_match >= 2:
                strengths.append("持有相关技能证书，专业能力获得认证")
            else:
                strengths.append("持有专业证书，学习态度积极")
        
        # 竞赛经历优势
        if has_competition:
            if skill_match >= 2:
                strengths.append("有竞赛获奖经历，技术能力和问题解决能力突出")
            else:
                strengths.append("参加过专业竞赛，具备创新思维和团队协作能力")
        
        # 软技能优势
        soft_skills = []
        if has_learning:       soft_skills.append("学习能力")
        if has_communication:  soft_skills.append("沟通协作")
        if has_pressure:       soft_skills.append("抗压能力")
        
        if len(soft_skills) >= 2:
            strengths.append(f"具备{' 和 '.join(soft_skills[:2])}等软技能")
        elif soft_skills:
            strengths.append(f"具备较强的{soft_skills[0]}")
        
        # 如果没有明显优势，给出鼓励性评价
        if not strengths:
            if sim > 0.4:
                strengths.append("简历内容与岗位方向基本匹配，有一定发展潜力")
            else:
                strengths.append("具备基础学习能力，可通过培训快速成长")

        # ── 3. 改进建议（✨ 个性化）────────────────────────────────────
        suggestions = []
        
        # 技能补充建议（根据缺失技能具体说明）
        if missing_skills:
            critical_skills = missing_skills[:3]
            if skill_coverage < 0.3:
                suggestions.append(f"建议重点学习岗位核心技能：{', '.join(critical_skills)}，提升技能匹配度")
            elif skill_coverage < 0.6:
                suggestions.append(f"建议补充以下技能以提高竞争力：{', '.join(critical_skills)}")
            else:
                suggestions.append(f"可选择性学习：{', '.join(critical_skills)}，进一步完善技能体系")
        
        # 项目经验建议
        if not has_project:
            if matched_skills:
                suggestions.append(f"建议使用 {', '.join(matched_skills[:2])} 完成1-2个实战项目，增强实践经验")
            else:
                suggestions.append("建议补充课程项目、开源贡献或个人作品，展示技术能力")
        elif skill_match < 2:
            suggestions.append("建议在项目中多使用岗位相关技术栈，提升技术匹配度")
        
        # 实习经验建议
        if not has_internship:
            if skill_coverage >= 0.5:
                suggestions.append("技能基础较好，建议寻找相关实习机会，积累实战经验")
            else:
                suggestions.append("建议先通过项目实践提升技能，再寻找实习机会")
        
        # 证书建议
        if not has_certificate and skill_match >= 1:
            # 根据匹配的技能推荐证书
            cert_suggestions = []
            if any(s in matched_skills for s in ["python", "java", "c++"]):
                cert_suggestions.append("软考")
            if any(s in matched_skills for s in ["英语", "cet"]):
                cert_suggestions.append("英语四六级")
            if any(s in matched_skills for s in ["测试", "selenium"]):
                cert_suggestions.append("软件测试工程师认证")
            
            if cert_suggestions:
                suggestions.append(f"可考虑考取：{', '.join(cert_suggestions[:2])}，增强简历竞争力")
        
        # 竞赛建议
        if not has_competition and skill_match >= 2:
            suggestions.append("可参加蓝桥杯、ACM等编程竞赛，提升技术能力和简历亮点")
        
        # 综合建议
        if skill_coverage < 0.3 and not has_project and not has_internship:
            suggestions.append("建议先通过在线课程系统学习岗位技能，再通过项目实践巩固")
        
        # 如果已经很匹配，给出积极建议
        if skill_coverage >= 0.7 and has_project and (has_internship or has_competition):
            suggestions.append("简历匹配度高，建议重点准备面试，展示项目经验和技术深度")
        
        # 限制建议数量（最多3-4条）
        suggestions = suggestions[:4]

        return {
            "matched_skills":  matched_skills,
            "missing_skills":  missing_skills,
            "skill_coverage":  round(skill_coverage, 3),
            "title_kw_score":  round(title_kw, 3),
            "industry_match":  round(industry_match, 3),
            "reasons":         reasons,
            "strengths":       strengths,
            "suggestions":     suggestions,
        }

    # ── 主入口 ────────────────────────────────────────────────────────────
    def recommend(self, resume_text, recall_k=100, topn=20):
        resume_vec = self.model.encode(
            [resume_text], normalize_embeddings=True
        )[0].astype(np.float32)

        idxs, sims = self.recall(resume_text, resume_vec, topk=recall_k)
        if len(idxs) == 0:
            return []

        candidate_rows = [self.rows[i] for i in idxs]
        candidate_vecs = self.job_vectors[idxs]

        feats_df = self.rerank(
            resume_text=resume_text,
            resume_vec=resume_vec,
            candidate_rows=candidate_rows,
            candidate_vecs=candidate_vecs,
            candidate_sims=sims
        )

        out = []
        for _, r in feats_df.head(topn).iterrows():
            row_meta    = self.row_map[r["job_uuid"]]
            explanation = self._build_explanation(resume_text, row_meta, r)

            out.append({
                "uuid":     row_meta.uuid,
                "job_id":   row_meta.job_id,
                "title":    getattr(row_meta, "title", ""),
                "company":  getattr(row_meta, "company", ""),
                "address":  getattr(row_meta, "address", ""),
                "salary":   getattr(row_meta, "salary", ""),
                "industry": getattr(row_meta, "industry", ""),
                "work_time": getattr(row_meta, "work_time", ""),

                "sim":           float(r.get("sim", 0)),
                "rank_score":    float(r.get("rank_score", 0)),
                "skill_match":   int(r.get("skill_match", 0)),
                "skill_jaccard": float(r.get("skill_jaccard", 0)),
                "skill_coverage": float(r.get("skill_coverage", 0)),
                "title_kw_score": float(r.get("title_kw_score", 0)),
                "industry_match": float(r.get("industry_match", 0)),

                "has_internship":             int(r.get("has_internship", 0)),
                "has_certificate":            int(r.get("has_certificate", 0)),
                "has_project":                int(r.get("has_project", 0)),
                "has_competition":            int(r.get("has_competition", 0)),
                "has_learning_evidence":      int(r.get("has_learning_evidence", 0)),
                "has_communication_evidence": int(r.get("has_communication_evidence", 0)),
                "has_pressure_evidence":      int(r.get("has_pressure_evidence", 0)),

                "explanation": explanation,
            })

        return out

def main(args):
    engine = RecommendationEngine(
        model_path=args.model_path,
        db_uri=args.db_uri,
        lgb_model_path=args.lgb_model,
        faiss_index_path=args.faiss_index_path
    )
    engine.load()
    result = engine.recommend(
        resume_text=args.resume_text,
        recall_k=args.recall_k,
        topn=args.topn
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model_path",       required=True)
    p.add_argument("--db_uri",           default="sqlite:///jobs.db")
    p.add_argument("--resume_text",      required=True)
    p.add_argument("--recall_k",         type=int, default=100)
    p.add_argument("--topn",             type=int, default=20)
    p.add_argument("--lgb_model",        default=None)
    p.add_argument("--faiss_index_path", default="./models/job_faiss.index")
    args = p.parse_args()
    main(args)