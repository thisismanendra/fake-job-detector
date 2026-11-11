"""Online verification: does the company/job link look real on the internet?

All checks fail gracefully (offline / blocked network just yields 'unknown'),
so the rest of the pipeline keeps working.
"""
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .config import REQUEST_TIMEOUT, USER_AGENT

try:
    import tldextract
except ImportError:  # optional
    tldextract = None
try:
    import whois  # python-whois
except ImportError:  # optional
    whois = None

HEADERS = {"User-Agent": USER_AGENT}
SUSPICIOUS_TLDS = {"xyz", "top", "club", "online", "site", "work", "click", "loan", "icu"}
JOB_PORTALS = ("linkedin.com", "naukri.com", "indeed.com", "glassdoor", "foundit", "internshala.com",
               "wellfound.com", "monster")


@dataclass
class OnlineResult:
    risk: float                      # 0 (looks real) .. 1 (looks fake); 0.5 = unknown
    findings: list = field(default_factory=list)
    checked: bool = False            # True if at least one check could be completed


def _registered_domain(url_or_host: str) -> str:
    host = urlparse(url_or_host if "//" in url_or_host else "//" + url_or_host).hostname or ""
    if tldextract:
        ext = tldextract.extract(host)
        return ".".join(p for p in (ext.domain, ext.suffix) if p)
    return ".".join(host.split(".")[-2:])


def domain_age_days(domain: str):
    if not whois:
        return None
    try:
        info = whois.whois(domain)
        created = info.creation_date
        if isinstance(created, list):
            created = created[0]
        if created is None:
            return None
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created).days
    except Exception:
        return None


def check_website(url: str):
    """Return (reachable, https, page_text) for a URL."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(" ").split())[:5000]
        return (r.status_code < 400, r.url.startswith("https://"), text)
    except requests.RequestException:
        return (False, url.startswith("https://"), "")


def fetch_job_page_text(url: str) -> str:
    """Scrape visible text from a job link so the ML model can analyse it."""
    _, _, text = check_website(url)
    return text


def internet_available() -> bool:
    """Quick connectivity test so 'no internet' is never mistaken for 'fake company'."""
    for host in ("www.google.com", "www.wikipedia.org"):
        try:
            socket.gethostbyname(host)
            return True
        except OSError:
            continue
    return False


def verify_online(company_name: str = "", company_website: str = "", job_url: str = "") -> OnlineResult:
    findings, risk_points, checks_done = [], 0.0, 0

    if (company_website or job_url) and not internet_available():
        return OnlineResult(risk=0.5, checked=False,
                            findings=["No internet connection - online verification skipped."])

    # 1) Company website checks
    if company_website:
        if not company_website.startswith("http"):
            company_website = "https://" + company_website
        domain = _registered_domain(company_website)

        try:
            socket.gethostbyname(urlparse(company_website).hostname)
            dns_ok = True
        except Exception:
            dns_ok = False
        checks_done += 1

        if not dns_ok:
            risk_points += 0.6
            findings.append(f"Company domain '{domain}' does not resolve (site may not exist).")
        else:
            ok, https, text = check_website(company_website)
            checks_done += 1
            if not ok:
                risk_points += 0.3
                findings.append("Company website is unreachable or returns an error.")
            if not https:
                risk_points += 0.15
                findings.append("Company website does not use HTTPS.")
            if ok and company_name:
                key = company_name.lower().split()[0]
                if key not in text.lower():
                    risk_points += 0.2
                    findings.append("Company name not found on the company's own website.")
                else:
                    findings.append("Company name appears on the company website. (good sign)")
            if ok and not re.search(r"careers?|jobs?|join\s+us|work\s+with\s+us", text, re.I):
                risk_points += 0.05
                findings.append("Website has no visible careers/jobs section.")

        tld = domain.split(".")[-1] if domain else ""
        if tld in SUSPICIOUS_TLDS:
            risk_points += 0.2
            findings.append(f"Domain uses a TLD ('.{tld}') often seen in scam sites.")

        age = domain_age_days(domain)
        if age is not None:
            checks_done += 1
            if age < 180:
                risk_points += 0.35
                findings.append(f"Company domain is very new ({age} days old).")
            else:
                findings.append(f"Company domain age: ~{age // 365} years. (good sign)")

    # 2) Job link checks
    if job_url:
        host = urlparse(job_url if "//" in job_url else "//" + job_url).hostname or ""
        checks_done += 1
        if any(p in host for p in JOB_PORTALS):
            findings.append(f"Posted on a known job portal ({host}). Still verify the employer.")
        else:
            risk_points += 0.1
            findings.append(f"Job link is not on a well-known portal or the company site ({host}).")

    if checks_done == 0:
        return OnlineResult(risk=0.5, findings=["No website/link supplied - online verification skipped."],
                            checked=False)
    return OnlineResult(risk=min(risk_points, 1.0), findings=findings, checked=True)
