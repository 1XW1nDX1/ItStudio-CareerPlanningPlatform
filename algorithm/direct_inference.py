from sentence_transformers import SentenceTransformer, util
import pandas as pd
import json

def main():
    # 1. 配置参数（和你的项目保持一致）
    MODEL_PATH = "paraphrase-multilingual-MiniLM-L12-v2"
    JOBS_CSV_PATH = "data/jobs.csv"  # 你的岗位数据文件
    RESUME_TEXT = "我有两年 PyTorch 项目经验，熟悉深度学习"  # 你的简历文本
    RECALL_K = 10  # 推荐前10个岗位

    # 2. 加载模型（和你的代码逻辑一致）
    print("正在加载模型...")
    model = SentenceTransformer(MODEL_PATH)
    print("模型加载完成！")

    # 3. 读取岗位数据（直接读CSV，不依赖数据库）
    print(f"正在读取岗位数据: {JOBS_CSV_PATH}")
    jobs_df = pd.read_csv(JOBS_CSV_PATH)
    print(f"成功读取 {len(jobs_df)} 条岗位数据！")

    # 4. 生成向量并计算相似度（核心推荐逻辑）
    # 生成简历向量
    resume_embedding = model.encode(RESUME_TEXT, convert_to_tensor=True)
    
    # 生成所有岗位的向量并计算相似度
    results = []
    for idx, row in jobs_df.iterrows():
        job_id = row["job_id"]
        job_title = row["title"]
        job_desc = row["description"]
        job_full_text = f"{job_title}\n{job_desc}"  # 合并标题和描述
        
        # 生成岗位向量
        job_embedding = model.encode(job_full_text, convert_to_tensor=True)
        
        # 计算相似度（和你的代码逻辑一致）
        sim_score = util.cos_sim(resume_embedding, job_embedding).item()
        
        # 保存结果
        results.append({
            "uuid": f"job_{job_id}",  # 模拟UUID
            "job_text": job_full_text[:300] + "..." if len(job_full_text) > 300 else job_full_text,
            "sim": round(sim_score, 6),
            "lgb_score": None  # 简化版暂不包含LGB分数
        })

    # 5. 按相似度排序，取前K个
    results_sorted = sorted(results, key=lambda x: x["sim"], reverse=True)[:RECALL_K]

    # 6. 输出结果（和你的格式一致）
    print("\n=== 简历岗位推荐结果 ===")
    print(json.dumps(results_sorted, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()