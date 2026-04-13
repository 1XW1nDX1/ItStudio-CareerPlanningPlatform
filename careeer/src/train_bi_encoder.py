"""
Train a bi-encoder (dual-tower) using sentence-transformers.
Input CSV format (train_pairs.csv): resume_text,job_text,label
We use positive pairs (label==1) for MultipleNegativesRankingLoss.
"""
import argparse
import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
from torch.utils.data import DataLoader
import os

def load_positive_pairs(csv_path, max_samples=None):
    df = pd.read_csv(csv_path)
    pos = df[df['label'] == 1]
    if max_samples:
        pos = pos.sample(n=min(max_samples, len(pos)), random_state=42)
    examples = [InputExample(texts=[row['resume_text'], row['job_text']]) for _, row in pos.iterrows()]
    return examples

def main(args):
    # base model
    model = SentenceTransformer(args.model_name)

    train_examples = load_positive_pairs(args.train_csv, args.max_samples)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=args.batch_size)
    # uses in-batch negatives: MultipleNegativesRankingLoss
    train_loss = losses.MultipleNegativesRankingLoss(model)

    # Optionally, set up an evaluator on validation pairs
    if args.dev_csv and os.path.exists(args.dev_csv):
        dev_df = pd.read_csv(args.dev_csv)
        pairs = [(row['resume_text'], row['job_text']) for _, row in dev_df.iterrows()]
        scores = [row.get('label', 1) for _, row in dev_df.iterrows()]
        evaluator = evaluation.EmbeddingSimilarityEvaluator([p[0] for p in pairs],
                                                            [p[1] for p in pairs],
                                                            scores,
                                                            batch_size=args.batch_size)
    else:
        evaluator = None

    model.fit(train_objectives=[(train_dataloader, train_loss)],
              evaluator=evaluator,
              epochs=args.epochs,
              evaluation_steps=args.eval_steps if evaluator else None,
              output_path=args.out_dir,
              show_progress_bar=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_csv", required=True, help="CSV with resume_text,job_text,label")
    parser.add_argument("--dev_csv", default="", help="optional dev CSV for evaluator")
    parser.add_argument("--model_name", default="paraphrase-multilingual-MiniLM-L12-v2", help="base model")
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--eval_steps", type=int, default=500)
    args = parser.parse_args()
    main(args)