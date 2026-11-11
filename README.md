# Fake Job Detector

Checks whether a job posting is **genuine, suspicious or likely fake** using three signals:

| Signal | What it does | Weight |
|---|---|---|
| ML model | TF-IDF + Logistic Regression trained on labelled job postings | 50% |
| Red-flag rules | Detects fees, WhatsApp/Telegram contact, free-email recruiters, guaranteed jobs, etc. | 30% |
| Online verification | Company domain exists? HTTPS? Domain age? Company name on its own site? Job portal? | 20% |

## Project structure
```
fake_job_detector/
├── app.py                  # Streamlit web UI
├── main.py                 # Command-line interface
├── requirements.txt
├── data/                   # put fake_job_postings.csv here
├── models/                 # trained model is saved here
└── src/
    ├── config.py           # paths, weights, thresholds
    ├── make_sample_data.py # synthetic data for testing only
    ├── train.py            # trains + evaluates the model
    ├── rules.py            # red-flag rules
    ├── online_checks.py    # internet verification
    └── predict.py          # combines all signals into a verdict
```

## Setup
```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get the dataset (recommended)
#    Kaggle: "Real / Fake Job Posting Prediction" (EMSCAD)
#    Save as data/fake_job_postings.csv
#    No dataset yet? Generate a tiny test one:  python -m src.make_sample_data

# 4. Train
python -m src.train

# 5a. Command line
python main.py --company "ABC Jobs" --email "hr@gmail.com" --text "Pay Rs 1000 registration fee..."
python main.py --offline --text "..."      # skip internet checks

# 5b. Web app
streamlit run app.py
```

## Important notes
- The sample data is synthetic, so its 100% accuracy means nothing. Train on the real EMSCAD
  dataset and report **recall / F1 / ROC-AUC on the Fake class**, not plain accuracy (the data is ~95% genuine).
- Online checks are skipped automatically when there is no internet.
- `python-whois` and `tldextract` are optional; without them domain-age/TLD parsing is simplified.
- This is decision support, not proof. Tune weights/thresholds in `src/config.py`.

## Ideas for improvement
1. Better model: XGBoost/LightGBM with extra features, or a BERT fine-tune.
2. Add structured features (telecommuting, has_company_logo, employment_type) from the dataset.
3. Search APIs (Google Custom Search / SerpAPI) to look for scam reports about the company.
4. Check company registration (MCA India, LinkedIn page, Glassdoor reviews).
5. Browser extension or Telegram bot front end.
6. Collect user feedback and retrain.
