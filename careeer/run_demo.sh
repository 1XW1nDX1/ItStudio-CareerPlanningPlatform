#!/usr/bin/env bash
set -e
# Demo script (Linux/macOS). 调整 python 可执行路径为 python3 如需。
python -m pip install -r requirements.txt

# 1) 将岗位编码写入 SQLite
python src/encode_jobs_db.py --jobs_csv data/jobs.csv --model_name paraphrase-multilingual-MiniLM-L12-v2 --db_uri sqlite:///jobs.db

# 2) （可选）训练 LightGBM（这里用示例 CSV）
python src/train_lgb.py --features_csv data/features_example.csv --out_dir models/lgb --objective binary

# 3) 推理示例（不带 LGB）
python src/inference_pipeline_db.py --model_path paraphrase-multilingual-MiniLM-L12-v2 --db_uri sqlite:///jobs.db --resume_text "我有两年 PyTorch 项目经验，熟悉深度学习" --recall_k 10

# 4) 推理示例（带 LGB，如果训练过）
# python src/inference_pipeline_db.py --model_path paraphrase-multilingual-MiniLM-L12-v2 --db_uri sqlite:///jobs.db --resume_text "我有两年 PyTorch 项目经验，熟悉深度学习" --recall_k 10 --lgb_model models/lgb/lgb_model.joblib