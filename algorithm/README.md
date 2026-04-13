1.项目简介

基于Sentence-BERT 文本语义向量 + LightGBM 排序模型的简历 - 职位匹配推荐系统。
输入：用户简历文本
输出：Top-K 最匹配职位列表（含相似度 / 排序分数）

2.环境依赖

Python 3.10+
依赖安装：
bash
运行
pip install -r requirements.txt


3.启动命令

可能会出现SSL认证问题
$env:HF_ENDPOINT = "https://hf-mirror.com"
python src/inference_pipeline_db.py 
    --model_path "./models/paraphrase-multilingual-MiniLM-L12-v2" `
    --db_uri "sqlite:///jobs.db" `
    --resume_text "我有两年PyTorch项目经验，熟悉深度学习、推荐系统" `(输入格式)
    --recall_k 10



4.输入参数说明

参数	说明	示例
--model_path	句向量模型路径	./models/...-L12-v2
--db_uri	数据库地址	sqlite:///jobs.db
--resume_text	简历 / 用户描述	字符串
--recall_k	返回职位数量	10

5. 输出格式（JSON 结构）
json
[
    {
        "job_uuid":"02f9600c-554c-481b-8c9b-e6b7437fdd17",
        "sim": 0.85234072351051803,
        "skill_match": 3,
        "years_diff": 0
    },
    ...
]
6. 模型说明

Embedding 模型：paraphrase-multilingual-MiniLM-L12-v2
首次运行会自动下载模型(时间可能较长)
功能：将文本转为语义向量
Rank 模型：LightGBM
功能：对召回结果精排，提升匹配准确度

7.api
extract_skills_from_resume_text(resume_text)：提取简历技能词
count_skill_matches(resume_skills, job_skill_tokens)：计算技能匹配数
extract_experience_years(text)：提取简历工作年限
build_features_from_db(resume_text, resume_vec, candidates_meta_rows, candidate_vecs)：生成精排特征（核心，给 LightGBM 提供输入）

接口地址：http://localhost:8000/api/recommend
