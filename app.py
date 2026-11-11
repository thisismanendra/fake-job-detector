
"""Streamlit web UI. Run: streamlit run app.py"""

import streamlit as st

from src.predict import analyze_job


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Fake Job Detector",
    page_icon="🕵️",
    layout="centered"
)

st.title("🕵️ Fake Job Detector")

st.caption(
    "Analyze job postings using Machine Learning, "
    "red-flag rules and online verification."
)

st.divider()


# --------------------------------------------------
# JOB INFORMATION FORM
# --------------------------------------------------

with st.form("job_form"):

    st.subheader("📋 Enter Job Details")

    company = st.text_input(
        "Company Name",
        placeholder="Enter company name"
    )

    website = st.text_input(
        "Company Website (optional)",
        placeholder="https://company.com"
    )

    email = st.text_input(
        "Recruiter Email (optional)",
        placeholder="recruiter@company.com"
    )

    job_url = st.text_input(
        "Job Posting Link (optional)",
        placeholder="Paste job posting URL"
    )

    text = st.text_area(
        "Job Description",
        height=220,
        placeholder="Paste the complete job description here..."
    )

    online = st.checkbox(
        "Run internet verification",
        value=True
    )

    submitted = st.form_submit_button(
        "🔍 Analyze Job",
        use_container_width=True
    )


# --------------------------------------------------
# JOB ANALYSIS
# --------------------------------------------------

if submitted:

    if not text.strip() and not job_url.strip():

        st.warning(
            "Please paste a job description or provide a job link."
        )

    else:

        try:

            with st.spinner("🤖 Analyzing job posting..."):

                v = analyze_job(
                    text,
                    company,
                    website,
                    email,
                    job_url,
                    use_online=online
                )

            # ------------------------------------------
            # FINAL VERDICT
            # ------------------------------------------

            st.divider()
            st.subheader("📊 Analysis Results")

            colors = {
                "GENUINE": "green",
                "SUSPICIOUS": "orange",
                "LIKELY FAKE": "red"
            }

            colour = colors.get(v.label, "gray")

            st.markdown(
                f"## Verdict: :{colour}[{v.label}]"
            )

            # ------------------------------------------
            # RISK SCORE
            # ------------------------------------------

            risk = max(
                0.0,
                min(float(v.risk_score), 1.0)
            )

            st.progress(
                risk,
                text=f"Overall Risk Score: {risk:.0%}"
            )

            # ------------------------------------------
            # COMPONENT SCORES
            # ------------------------------------------

            st.subheader("Detection Component Scores")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "🤖 ML Model",
                f"{v.ml_score:.2f}"
            )

            c2.metric(
                "⚠️ Red-Flag Rules",
                f"{v.rule_score:.2f}"
            )

            c3.metric(
                "🌐 Online Check",
                f"{v.online_score:.2f}"
            )

            # ------------------------------------------
            # RED FLAGS
            # ------------------------------------------

            st.divider()
            st.subheader("⚠️ Red Flags")

            if v.red_flags:

                for flag in v.red_flags:
                    st.warning(flag)

            else:

                st.success("No red flags were identified.")

            # ------------------------------------------
            # ONLINE FINDINGS
            # ------------------------------------------

            st.subheader("🌐 Online Findings")

            if v.online_findings:

                for finding in v.online_findings:
                    st.info(finding)

            elif online:

                st.write("No additional online findings were returned.")

            else:

                st.write("Online verification was disabled.")

            # ------------------------------------------
            # SAFETY MESSAGE
            # ------------------------------------------

            st.divider()

            st.info(
                "This tool supports your decision but cannot "
                "guarantee that a job is genuine. "
                "Always independently verify the company. "
                "Never pay money to obtain employment."
            )

        except Exception as e:

            st.error(f"Analysis failed: {e}")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "🕵️ Fake Job Detector | Powered by Python, "
    "Machine Learning and Streamlit"
)
