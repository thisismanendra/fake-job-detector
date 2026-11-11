"""Command-line interface.

Examples:
    python main.py --text "Earn Rs 5000/day, pay registration fee..." --company "ABC Jobs"
    python main.py --file job.txt --website https://example.com --email hr@example.com
    python main.py --url https://careers.example.com/job/123 --offline
"""
import argparse

from src.predict import analyze_job


def main():
    p = argparse.ArgumentParser(description="Fake Job Detector")
    p.add_argument("--text", default="", help="Job description text")
    p.add_argument("--file", help="Path to a .txt file with the job description")
    p.add_argument("--company", default="")
    p.add_argument("--website", default="", help="Company website")
    p.add_argument("--email", default="", help="Recruiter contact email")
    p.add_argument("--url", default="", help="Link to the job posting")
    p.add_argument("--offline", action="store_true", help="Skip internet checks")
    a = p.parse_args()

    text = a.text
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            text = f.read()

    v = analyze_job(text, a.company, a.website, a.email, a.url, use_online=not a.offline)

    print("\n" + "=" * 55)
    print(f"  VERDICT: {v.label}   (risk score {v.risk_score:.0%})")
    print("=" * 55)
    print(f"  ML model score : {v.ml_score:.2f}")
    print(f"  Rule score     : {v.rule_score:.2f}")
    print(f"  Online score   : {v.online_score:.2f}")
    if v.red_flags:
        print("\nRed flags:")
        for f in v.red_flags:
            print("  - " + f)
    if v.online_findings:
        print("\nOnline findings:")
        for f in v.online_findings:
            print("  - " + f)
    print("\nNote: this is a decision-support tool, not a guarantee. Always verify the employer independently.")


if __name__ == "__main__":
    main()
