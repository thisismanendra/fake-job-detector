"""Generate a small synthetic dataset so the pipeline can run without downloading anything.

This is ONLY for testing the code. For real accuracy, use the EMSCAD dataset
(Kaggle: "Real / Fake Job Posting Prediction") saved as data/fake_job_postings.csv.
The column layout below mirrors that dataset.
"""
import random

import pandas as pd

from .config import DATA_DIR, SAMPLE_DATASET

random.seed(42)

REAL_TITLES = ["Software Engineer", "Data Analyst", "Junior Python Developer", "QA Engineer",
               "Marketing Executive", "Accountant", "HR Associate", "Backend Developer"]
REAL_COMPANIES = ["Infosys", "TCS", "Wipro", "Zoho", "Freshworks", "Accenture", "Capgemini", "Tech Mahindra"]
REAL_DESC = [
    "We are looking for a {t} to join our team. Responsibilities include designing, developing and testing "
    "applications, collaborating with cross-functional teams and participating in code reviews. "
    "Requirements: Bachelor's degree in Computer Science or related field, 1-3 years of relevant experience, "
    "strong communication skills. We offer health insurance, learning budget and hybrid work. "
    "Apply through our official careers page. Interview process includes technical and HR rounds.",
    "{c} is hiring a {t}. You will work with senior engineers on production systems, write clean maintainable "
    "code and contribute to documentation. Qualifications: degree in engineering, knowledge of SQL and Python, "
    "ability to work in agile teams. Benefits include paid leave, provident fund and career growth plans. "
    "Submit your resume on careers.{d}.com. Shortlisted candidates will be contacted by our recruitment team.",
    "Position: {t} at {c}. Duties: analyse requirements, deliver features on schedule, support the team and "
    "maintain quality standards. Skills: problem solving, teamwork, good written English. Salary as per "
    "industry standards and experience. Selection involves an online assessment followed by two interviews.",
]

FAKE_DESC = [
    "URGENT HIRING!!! Work from home data entry job. No experience required. Earn Rs 5000 per day easily. "
    "100% job guarantee. Pay registration fee Rs 1500 to confirm your seat. Contact us on WhatsApp now! "
    "Offer letter sent immediately after payment.",
    "Earn lakhs from home! Simple copy paste work, no interview, direct joining. Limited seats, apply now!!! "
    "Send security deposit to receive your kit. Telegram: t.me/earnfast. Email: hr.jobs2024@gmail.com",
    "Part time work from home. Typing job, form filling job. No qualification needed. Daily payment guaranteed. "
    "Training fee Rs 999 refundable. Contact on WhatsApp 9876543210. Instant joining. Hurry up!",
    "Dear candidate you are selected for {t}. Confirmation letter will be issued after you pay processing charges. "
    "Make money online, easy money, 100% placement. Reply to recruiter.hiring@yahoo.com urgently.",
    "Urgent requirement for {t}. Salary $4000 per week. No experience needed. Send bank details required to "
    "set up payroll. Interview not required. Apply on forms.gle/abc123",
]


def build(n_real=300, n_fake=60):
    rows = []
    for _ in range(n_real):
        c = random.choice(REAL_COMPANIES)
        t = random.choice(REAL_TITLES)
        d = c.lower().replace(" ", "")
        desc = random.choice(REAL_DESC).format(t=t, c=c, d=d)
        rows.append(dict(title=t, company_profile=f"{c} is a leading technology company.",
                         description=desc, requirements="Degree and relevant skills.",
                         benefits="Health insurance, paid leave", fraudulent=0))
    for _ in range(n_fake):
        t = random.choice(REAL_TITLES + ["Data Entry Operator", "Home Based Typist", "Online Form Filler"])
        desc = random.choice(FAKE_DESC).format(t=t)
        rows.append(dict(title=t, company_profile="", description=desc,
                         requirements="", benefits="Daily payment", fraudulent=1))
    df = pd.DataFrame(rows).sample(frac=1, random_state=1).reset_index(drop=True)
    return df


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    df = build()
    df.to_csv(SAMPLE_DATASET, index=False)
    print(f"Saved {len(df)} rows -> {SAMPLE_DATASET}")
