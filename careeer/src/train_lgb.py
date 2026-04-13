"""
Train LightGBM model given features CSV including label and optional group id (for lambdarank).
Expected features CSV columns: label, group (optional), feature1, feature2, ...
"""
import argparse
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import joblib
import os

def main(args):
    df = pd.read_csv(args.features_csv)
    features = [c for c in df.columns if c not in ('label','group')]
    X = df[features]
    y = df['label']
    if args.objective == 'lambdarank':
        if 'group' not in df.columns:
            raise ValueError("group column required for lambdarank objective")
        grouped = df['group']
        # train-test split by group to avoid leakage
        groups = grouped.unique().tolist()
        train_groups, val_groups = train_test_split(groups, test_size=0.2, random_state=42)
        train_idx = df['group'].isin(train_groups)
        val_idx = df['group'].isin(val_groups)
        dtrain = lgb.Dataset(X[train_idx], label=y[train_idx], group=grouped[train_idx].values)
        dval = lgb.Dataset(X[val_idx], label=y[val_idx], group=grouped[val_idx].values, reference=dtrain)
        params = {
            'objective':'lambdarank',
            'metric':'ndcg',
            'ndcg_eval_at':[1,3,5],
            'learning_rate':0.05,
            'num_leaves':31,
            'min_data_in_leaf':20
        }
        bst = lgb.train(params, dtrain, valid_sets=[dval], early_stopping_rounds=50, num_boost_round=1000)
    else:
        # binary classification/regression
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        dtrain = lgb.Dataset(X_train, label=y_train)
        dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
        params = {
            'objective':'binary',
            'metric':'auc',
            'learning_rate':0.05,
            'num_leaves':31
        }
        bst = lgb.train(params, dtrain, valid_sets=[dval], callbacks=[lgb.early_stopping(50)], num_boost_round=1000)

    os.makedirs(args.out_dir, exist_ok=True)
    joblib.dump({'model':bst, 'features':features}, os.path.join(args.out_dir, "lgb_model.joblib"))
    print("Saved LightGBM model to", args.out_dir)

if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--features_csv", required=True)
    p.add_argument("--out_dir", required=True)
    p.add_argument("--objective", choices=['binary','lambdarank'], default='binary')
    args = p.parse_args()
    main(args)