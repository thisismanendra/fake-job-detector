"""Rule-based red-flag detection for job postings.

Each rule has a weight. The final rule score is the (capped) sum of weights
of all triggered rules, giving a value between 0 and 1.
"""
import re
from dataclasses import dataclass

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com",
    "rediffmail.com", "protonmail.com", "aol.com", "mail.com",
}

# (name, regex, weight, explanation)
PATTERN_RULES = [
    ("asks_for_payment",
     r"(registration|security|training|processing|kit|application|refundable)\s+(fee|deposit|charges?|amount)|"
     r"pay\s+(rs\.?|inr|\$|₹)?\s*\d+|deposit\s+(rs\.?|inr|\$|₹)?\s*\d+|send\s+money|"
     r"bank\s+(details|account)\s+(required|needed)",
     0.45, "Asks the candidate to pay money (fees/deposit). Genuine employers never charge."),
    ("chat_app_contact",
     r"whats\s?app|telegram|signal\s+app|text\s+us\s+on|contact\s+(us\s+)?on\s+\d{10}",
     0.25, "Asks to continue on WhatsApp/Telegram instead of official channels."),
    ("guaranteed_job",
     r"100%\s*(job\s*)?(guarantee|placement|selection)|guaranteed\s+(job|placement|selection)|"
     r"no\s+interview|direct\s+(joining|selection)|instant\s+(joining|offer)",
     0.30, "Promises guaranteed selection / no interview."),
    ("unrealistic_pay",
     r"earn\s+(up\s+to\s+)?(rs\.?|inr|\$|₹)?\s*\d{2,3}[,\d]*\s*(/|per)\s*(day|week|hour)|"
     r"(rs\.?|₹|\$)\s*\d{4,6}\s*(/|per)\s*(day|daily)|earn\s+lakhs|"
     r"make\s+money\s+(from\s+home|online)|easy\s+money",
     0.30, "Unrealistically high / easy earnings."),
    ("no_experience_high_pay",
     r"no\s+(experience|skills?|qualification)\s+(needed|required|necessary)",
     0.12, "No experience or skills required (common in scams)."),
    ("urgency",
     r"urgent(ly)?\s+(hiring|requirement|opening)|limited\s+(seats|vacancies|slots)|apply\s+(now|immediately|today)\s*!+|"
     r"hurry|last\s+date\s+today",
     0.12, "Pressure/urgency language."),
    ("work_from_home_generic",
     r"(data\s+entry|copy\s*paste|form\s+filling|typing)\s+(job|work)|part[-\s]?time\s+work\s+from\s+home",
     0.15, "Generic data-entry / work-from-home pitch often used in scams."),
    ("fake_offer_letter",
     r"offer\s+letter\s+(will\s+be\s+)?(sent|issued)\s+(immediately|instantly|on\s+payment)|"
     r"confirmation\s+letter",
     0.20, "Offer letter promised before any interview/verification."),
    ("shortened_or_form_link",
     r"bit\.ly|tinyurl|t\.me/|forms\.gle|docs\.google\.com/forms|wa\.me/",
     0.15, "Uses shortened / form / chat links instead of a company careers page."),
    ("vague_description",
     r"^.{0,120}$",
     0.15, "Job description is extremely short/vague."),
]

EMAIL_RE = re.compile(r"[\w.\-+]+@([\w\-]+\.[\w.\-]+)")
CAPS_RE = re.compile(r"\b[A-Z]{4,}\b")


@dataclass
class RuleResult:
    score: float
    flags: list  # list of (name, explanation)


def evaluate_rules(text: str, company_name: str = "", contact_email: str = "") -> RuleResult:
    text = text or ""
    flags = []
    total = 0.0

    for name, pattern, weight, explanation in PATTERN_RULES:
        flags_re = re.IGNORECASE | (re.DOTALL if name == "vague_description" else 0)
        if re.search(pattern, text.strip(), flags_re):
            total += weight
            flags.append((name, explanation))

    # Email checks (from explicit field + any email found in text)
    emails = set(EMAIL_RE.findall(text))
    if contact_email and "@" in contact_email:
        emails.add(contact_email.split("@")[-1].lower())
    emails = {e.lower() for e in emails}

    if emails & FREE_EMAIL_DOMAINS:
        total += 0.25
        flags.append(("free_email_domain",
                      "Contact email uses a free provider (gmail/yahoo...) instead of a company domain."))
    elif emails and company_name:
        key = re.sub(r"[^a-z0-9]", "", company_name.lower())[:6]
        if key and not any(key in re.sub(r"[^a-z0-9]", "", d) for d in emails):
            total += 0.15
            flags.append(("email_company_mismatch",
                          "Contact email domain does not match the company name."))

    # Shouting in ALL CAPS and excessive '!'
    if len(CAPS_RE.findall(text)) >= 8 or text.count("!") >= 4:
        total += 0.08
        flags.append(("shouting_style", "Excessive CAPS or exclamation marks."))

    if not company_name.strip():
        total += 0.10
        flags.append(("no_company_name", "No company name provided."))

    return RuleResult(score=min(total, 1.0), flags=flags)
