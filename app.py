import streamlit as st
import os
from groq import Groq

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Cybersecurity Assistant",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AI Cybersecurity Assistant")
st.caption("AI-powered security analysis, investigation and reporting toolkit")

# ============================================================
# API CONFIGURATION
# ============================================================

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

if not api_key:
    st.error(
        "⚠️ GROQ_API_KEY not configured.\n\n"
        "Set it as an environment variable or Streamlit secret."
    )
    st.stop()

client = Groq(api_key=api_key)

MODEL = "llama-3.3-70b-versatile"


# ============================================================
# HELPER FUNCTION
# ============================================================

def ask_ai(prompt, temperature=0.2):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """
You are an experienced cybersecurity analyst.

Your job is to help users understand security data,
logs, network traffic, vulnerabilities and defensive
investigations.

Rules:
1. Be technically accurate.
2. Clearly separate evidence from assumptions.
3. Never invent information that is not present in the input.
4. Explain technical terms when useful.
5. Prefer practical defensive investigation steps.
6. For CTF/lab material, analysis and commands are allowed.
7. Do not claim that a vulnerability exists unless the evidence
   supports it.
8. When uncertain, explicitly say what additional information
   would be required.
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ API Error: {str(e)}"


# ============================================================
# TABS
# ============================================================

tabs = st.tabs([
    "🔍 Log Analyzer",
    "🌐 Nmap Analyzer",
    "📡 HTTP Analyzer",
    "🧠 KQL Generator",
    "🚨 Alert Analyzer",
    "📝 Report Generator"
])


# ============================================================
# TAB 1 - LOG ANALYZER
# ============================================================

with tabs[0]:

    st.header("🔍 Security Log Analyzer")

    st.write(
        "Paste authentication, web server, firewall, Linux, "
        "Windows or application logs and identify suspicious activity."
    )

    log_type = st.selectbox(
        "Log Type",
        [
            "Linux Authentication",
            "Windows Security",
            "Web Server",
            "Firewall",
            "DNS",
            "Application",
            "Unknown"
        ]
    )

    logs = st.text_area(
        "Paste Logs",
        height=350,
        placeholder="Paste security logs here..."
    )

    if st.button("🔎 Analyze Logs", type="primary"):

        if not logs.strip():
            st.warning("Please provide logs.")
        else:

            prompt = f"""
Analyze the following {log_type} logs.

Provide the response using these sections:

## 1. Executive Summary

## 2. Important Events

## 3. Suspicious Indicators
Include:
- IP addresses
- usernames
- domains
- URLs
- ports
- processes
- timestamps
- error messages

Only include indicators actually present in the logs.

## 4. Possible Attack Techniques

Map suspicious activity to likely MITRE ATT&CK
techniques where reasonable.

## 5. Timeline

Create a chronological investigation timeline.

## 6. Severity

Classify findings as:
- Critical
- High
- Medium
- Low
- Informational

Explain why.

## 7. Recommended Investigation

Give defensive investigation steps.

LOGS:

{logs}
"""

            with st.spinner("Analyzing security logs..."):
                result = ask_ai(prompt)

            st.success("Analysis complete")
            st.markdown(result)


# ============================================================
# TAB 2 - NMAP ANALYZER
# ============================================================

with tabs[1]:

    st.header("🌐 Nmap Output Analyzer")

    st.write(
        "Paste authorized Nmap scan output and get a structured "
        "security assessment."
    )

    target = st.text_input(
        "Target / Lab Name",
        placeholder="e.g. Internal Lab Server"
    )

    nmap_output = st.text_area(
        "Nmap Output",
        height=350,
        placeholder="Paste nmap output here..."
    )

    if st.button("🔎 Analyze Nmap", type="primary"):

        if not nmap_output.strip():
            st.warning("Please provide Nmap output.")
        else:

            prompt = f"""
Analyze this Nmap result from an authorized security assessment.

Target:
{target}

Nmap output:
{nmap_output}

Produce:

# 1. Scan Summary

# 2. Open Ports

Create a table containing:

| Port | Protocol | Service | Version | Risk |

Only use information present in the scan.

# 3. Interesting Services

Explain why each exposed service deserves attention.

# 4. Potential Security Concerns

Identify plausible security concerns based on the
detected services and versions.

Do not claim exploitation is possible without evidence.

# 5. Recommended Validation

Provide safe, authorized validation steps for each
interesting service.

# 6. Hardening Recommendations

Give defensive recommendations.

# 7. Priority

Rank the most important findings from highest to lowest.
"""

            with st.spinner("Analyzing Nmap output..."):
                result = ask_ai(prompt)

            st.markdown(result)


# ============================================================
# TAB 3 - HTTP ANALYZER
# ============================================================

with tabs[2]:

    st.header("📡 HTTP Request / Response Analyzer")

    st.write(
        "Analyze HTTP traffic captured during an authorized "
        "security assessment or CTF."
    )

    http_data = st.text_area(
        "HTTP Request / Response",
        height=450,
        placeholder="""GET /login HTTP/1.1
Host: example.local
Cookie: session=...
User-Agent: ...

HTTP/1.1 200 OK
Content-Type: text/html
..."""
    )

    if st.button("🔎 Analyze HTTP", type="primary"):

        if not http_data.strip():
            st.warning("Please provide HTTP traffic.")
        else:

            prompt = f"""
Analyze the following HTTP request/response.

{http_data}

Return:

## 1. Request Summary

## 2. Response Summary

## 3. Interesting Headers

Discuss headers such as:
- Cookie
- Authorization
- Host
- Origin
- Referer
- Content-Type
- Server
- Security headers

## 4. Authentication / Session Observations

## 5. Potential Security Issues

Consider common web security categories such as:
- Authentication weaknesses
- Authorization issues
- Session management
- Input validation
- Information disclosure
- Security header issues
- CORS configuration

Do not claim a vulnerability merely because a header
or parameter exists.

## 6. CTF Investigation Ideas

If this appears to be CTF traffic, list reasonable
next investigation steps.

## 7. Defensive Recommendations
"""

            with st.spinner("Analyzing HTTP traffic..."):
                result = ask_ai(prompt)

            st.markdown(result)


# ============================================================
# TAB 4 - KQL GENERATOR
# ============================================================

with tabs[3]:

    st.header("🧠 Natural Language → KQL")

    st.write(
        "Describe the investigation you want to perform and "
        "generate a Microsoft Sentinel / Defender-style KQL query."
    )

    available_tables = st.text_input(
        "Available Tables",
        placeholder="e.g. DnsEvents, NetworkFlow, Email, AuthenticationEvents"
    )

    request = st.text_area(
        "Describe Your Investigation",
        height=200,
        placeholder=(
            "Example: Find clients that contacted a suspicious "
            "domain and show their first and last communication."
        )
    )

    if st.button("⚡ Generate KQL", type="primary"):

        if not request.strip():
            st.warning("Please describe the query you want.")
        else:

            prompt = f"""
You are a Microsoft Sentinel KQL expert.

Available tables:

{available_tables}

User requirement:

{request}

Generate:

## KQL Query

Put the complete query inside a code block.

## Explanation

Explain the query line by line.

## Expected Output

Explain what each important output column represents.

## Possible Improvements

Suggest useful filters or extensions.

Important:
- Do not invent columns if the user has supplied a schema.
- If a required column is unknown, clearly identify it as an assumption.
- Prefer readable KQL.
"""

            with st.spinner("Generating KQL..."):
                result = ask_ai(prompt, temperature=0.1)

            st.markdown(result)


# ============================================================
# TAB 5 - ALERT ANALYZER
# ============================================================

with tabs[4]:

    st.header("🚨 Security Alert Analyzer")

    alert_name = st.text_input(
        "Alert Name",
        placeholder="Suspicious PowerShell Execution"
    )

    alert_data = st.text_area(
        "Alert Details",
        height=350,
        placeholder="Paste SIEM/EDR alert details..."
    )

    if st.button("🚨 Investigate Alert", type="primary"):

        if not alert_data.strip():
            st.warning("Please provide alert details.")
        else:

            prompt = f"""
Analyze this security alert.

Alert:
{alert_name}

Details:
{alert_data}

Produce a SOC-style investigation:

## 1. Alert Summary

## 2. Evidence

List only evidence present in the alert.

## 3. Severity Assessment

Explain the reasoning.

## 4. Possible Attack Scenario

Describe the most likely interpretation,
while clearly labeling assumptions.

## 5. MITRE ATT&CK Mapping

Provide likely techniques when supported.

## 6. Investigation Checklist

Provide concrete defensive investigation steps.

## 7. Useful Queries

Suggest example SIEM/EDR queries where appropriate.

## 8. Containment Considerations

Describe defensive containment options.

## 9. False Positive Possibilities

List legitimate explanations that should be ruled out.
"""

            with st.spinner("Investigating alert..."):
                result = ask_ai(prompt)

            st.markdown(result)


# ============================================================
# TAB 6 - REPORT GENERATOR
# ============================================================

with tabs[5]:

    st.header("📝 Security Finding / Report Generator")

    finding_title = st.text_input(
        "Finding Title",
        placeholder="Exposed Administrative Service"
    )

    severity = st.selectbox(
        "Severity",
        ["Critical", "High", "Medium", "Low", "Informational"]
    )

    evidence = st.text_area(
        "Evidence",
        height=250,
        placeholder="Describe the evidence you collected..."
    )

    impact = st.text_area(
        "Impact",
        height=150,
        placeholder="What could this mean for the system?"
    )

    remediation = st.text_area(
        "Known Remediation",
        height=150,
        placeholder="Any remediation information you already have..."
    )

    if st.button("📄 Generate Report", type="primary"):

        if not finding_title or not evidence:
            st.warning("Finding title and evidence are required.")
        else:

            prompt = f"""
Create a professional cybersecurity finding.

Title:
{finding_title}

Severity:
{severity}

Evidence:
{evidence}

Potential Impact:
{impact}

Known Remediation:
{remediation}

Use this structure:

# {finding_title}

## Severity

## Executive Summary

## Technical Description

## Evidence

## Security Impact

## Reproduction / Validation

Describe only the validation supported by the supplied evidence.

## Remediation

## Detection Recommendations

## References / Mapping

If there is insufficient information for a section,
state what information is missing instead of inventing it.
"""

            with st.spinner("Generating security report..."):
                result = ask_ai(prompt)

            st.markdown(result)

            st.download_button(
                "⬇️ Download Report",
                result,
                file_name="security_finding.md",
                mime="text/markdown"
            )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🛡️ Cybersecurity Assistant")

    st.markdown("""
### Modules

🔍 Log Analysis  
🌐 Nmap Analysis  
📡 HTTP Analysis  
🧠 KQL Generation  
🚨 Alert Investigation  
📝 Security Reports  

---

### Usage

Use this application for:

- Security labs
- CTFs
- SOC investigations
- Log analysis
- Authorized penetration testing
- Security documentation

Always analyze systems and data you are
authorized to assess.
""")

    st.divider()

    st.caption(f"Model: {MODEL}")
