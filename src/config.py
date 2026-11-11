"""Central configuration for the Fake Job Detector."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "fake_job_model.joblib"

# Dataset: EMSCAD "Real / Fake Job Posting Prediction" (Kaggle).
# Download fake_job_postings.csv and place it in data/.
REAL_DATASET = DATA_DIR / "fake_job_postings.csv"
SAMPLE_DATASET = DATA_DIR / "sample_jobs.csv"

# Weights used when combining the three signals into one risk score (0-1).
WEIGHT_ML = 0.50
WEIGHT_RULES = 0.30
WEIGHT_ONLINE = 0.20

# Verdict thresholds on the final risk score.
FAKE_THRESHOLD = 0.60
SUSPICIOUS_THRESHOLD = 0.35

REQUEST_TIMEOUT = 8  # seconds
USER_AGENT = "Mozilla/5.0 (compatible; FakeJobDetector/1.0; student project)"
