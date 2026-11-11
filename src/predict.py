"""Combine ML + rules + online verification into one verdict."""
from dataclasses import dataclass, field

import joblib

from .config import (FAKE_THRESHOLD, MODEL_PATH, SUSPICIOUS_THRESHOLD,
                     WEIGHT_ML, WEIGHT_ONLINE, WEIGHT_RULES)
from .online_checks import fetch_job_page_text, verify_online
from .rules import evaluate_rules

_model = None


def _load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError("Model not trained yet. Run: python -m src.train")
        _model = joblib.load(MODEL_PATH)
    return _model


@dataclass
class Verdict:
    label: str                 # GENUINE / SUSPICIOUS / LIKELY FAKE
    risk_score: float          # 0..1
    ml_score: float
    rule_score: float
    online_score: float
    red_flags: list = field(default_factory=list)
    online_findings: list = field(default_factory=list)


def analyze_job(text: str = "", company_name: str = "", company_website: str = "",
                contact_email: str = "", job_url: str = "", use_online: bool = True) -> Verdict:
    # If only a link is given, scrape the page text
    if job_url and use_online and len(text.strip()) < 40:
        text = fetch_job_page_text(job_url if job_url.startswith("http") else "https://" + job_url)

    full_text = f"{company_name} {text}"
    ml = float(_load_model().predict_proba([full_text])[0][1])
    rules = evaluate_rules(text, company_name, contact_email)

    if use_online:
        online = verify_online(company_name, company_website, job_url)
    else:
        online = None

    # If online check could not run, redistribute its weight to the other signals
    if online is None or not online.checked:
        w_total = WEIGHT_ML + WEIGHT_RULES
        risk = (WEIGHT_ML * ml + WEIGHT_RULES * rules.score) / w_total
        online_score = 0.5 if online is None else online.risk
    else:
        risk = WEIGHT_ML * ml + WEIGHT_RULES * rules.score + WEIGHT_ONLINE * online.risk
        online_score = online.risk

    # Strong single red flags (payment demand) should never be 'averaged away'
    if any(n == "asks_for_payment" for n, _ in rules.flags):
        risk = max(risk, 0.75)

    if risk >= FAKE_THRESHOLD:
        label = "LIKELY FAKE"
    elif risk >= SUSPICIOUS_THRESHOLD:
        label = "SUSPICIOUS"
    else:
        label = "GENUINE"

    return Verdict(label=label, risk_score=round(risk, 3), ml_score=round(ml, 3),
                   rule_score=round(rules.score, 3), online_score=round(online_score, 3),
                   red_flags=[e for _, e in rules.flags],
                   online_findings=online.findings if online else [])
