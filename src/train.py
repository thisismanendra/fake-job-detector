"""Train the text classifier.

Usage:
    python -m src.train                      # uses data/fake_job_postings.csv if present, else sample data
    python -m src.train --data path/to.csv   # custom CSV
"""
import argparse

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .config import MODEL_DIR, MODEL_PATH, REAL_DATASET, SAMPLE_DATASET

TEXT_COLUMNS = ["title", "company_profile", "description", "requirements", "benefits"]


def load_dataset(path=None) -> pd.DataFrame:
    if path is None:
        path = REAL_DATASET if REAL_DATASET.exists() else SAMPLE_DATASET
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run: python -m src.make_sample_data")
    print(f"Loading dataset: {path}")
    df = pd.read_csv(path)
    for col in TEXT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df[TEXT_COLUMNS] = df[TEXT_COLUMNS].fillna("")
    df["text"] = df[TEXT_COLUMNS].agg(" ".join, axis=1)
    return df[["text", "fraudulent"]]


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                                  min_df=2, max_df=0.9, sublinear_tf=True)),
        # class_weight='balanced' handles the heavy imbalance (few fake jobs vs many real ones)
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", C=2.0)),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=None)
    args = parser.parse_args()

    from pathlib import Path
    df = load_dataset(Path(args.data) if args.data else None)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["fraudulent"], test_size=0.2, stratify=df["fraudulent"], random_state=42)

    model = build_pipeline()
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    print("\n=== Evaluation on held-out test set ===")
    print(classification_report(y_test, pred, target_names=["Genuine", "Fake"]))
    print("Confusion matrix [[TN FP] [FN TP]]:\n", confusion_matrix(y_test, pred))
    print("ROC-AUC:", round(roc_auc_score(y_test, proba), 4))

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
