import sys
import os
import re
import tempfile
import streamlit as st
from fpdf import FPDF

sys.path.append(os.path.dirname(__file__))
from agents.security_agent import build_agent  # noqa: E402
from tools.ocr_tool import extract_text_from_image  # noqa: E402


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CyberGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Custom CSS — dark, cyber-themed, colorful accents
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #0b0f1a 0%, #0f1730 100%);
        color: #e6f1ff;
    }

    .cg-header {
        padding: 1.5rem 2rem;
        border-radius: 16px;
        background: linear-gradient(90deg, #0ea5e9 0%, #7c3aed 100%);
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 24px rgba(14, 165, 233, 0.25);
    }
    .cg-header h1 { color: white; margin: 0; font-size: 2rem; }
    .cg-header p { color: #e0f2fe; margin: 0.25rem 0 0 0; }

    .cg-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(14, 165, 233, 0.25);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }

    .cg-badge {
        display: inline-block;
        padding: 0.25rem 0.9rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 0.4rem;
        letter-spacing: 0.03em;
    }
    .cg-badge-critical { background: #7f1d1d; color: #fecaca; }
    .cg-badge-high { background: #7c2d12; color: #fed7aa; }
    .cg-badge-medium { background: #713f12; color: #fef08a; }
    .cg-badge-low { background: #14532d; color: #bbf7d0; }
    .cg-badge-info { background: #0c4a6e; color: #bae6fd; }
    .cg-badge-ok { background: #14532d; color: #bbf7d0; }

    .cg-stat-box {
        background: rgba(255,255,255,0.04);
        border-radius: 10px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .cg-stat-num { font-size: 1.4rem; font-weight: 700; color: #7dd3fc; }
    .cg-stat-label { font-size: 0.75rem; color: #94a3b8; }

    div[data-testid="stSidebar"] {
        background: #0a0e1a;
        border-right: 1px solid rgba(124, 58, 237, 0.3);
    }

    .stTextArea textarea {
        background: rgba(255,255,255,0.05);
        color: #e6f1ff;
        border-radius: 10px;
    }

    .stButton button {
        background: linear-gradient(90deg, #0ea5e9, #7c3aed);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton button:hover { opacity: 0.9; }

    .cg-example-btn button {
        background: rgba(255,255,255,0.06);
        color: #e6f1ff;
        border: 1px solid rgba(148,163,184,0.3);
        font-weight: 500;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CREATOR_NAME = "Rifat"
GITHUB_LINK = "https://github.com/belal-rifat/cyberguard-ai"

SEVERITY_BADGE_CLASS = {
    "CRITICAL": "cg-badge-critical",
    "HIGH": "cg-badge-high",
    "MEDIUM": "cg-badge-medium",
    "LOW": "cg-badge-low",
}

EXAMPLE_QUERIES = {
    "📧 Phishing Email": (
        "I received an email saying my account will be blocked unless "
        "I verify it immediately by clicking a link."
    ),
    "🔒 Ransomware Alert": (
        "All files on my computer suddenly got renamed with a .locked "
        "extension and there's a README_TO_DECRYPT.txt file in every folder."
    ),
    "🔑 Brute Force Alert": (
        "Our server log shows 500 failed login attempts on the admin "
        "account in the last 10 minutes from different IP addresses."
    ),
}


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "agent" not in st.session_state:
    st.session_state.agent = build_agent()

if "history" not in st.session_state:
    st.session_state.history = []  # list of {query, severity, answer}

if "query_text" not in st.session_state:
    st.session_state.query_text = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def extract_answer_text(result) -> str:
    """Normalizes the agent's final message content into plain text,
    whether it comes back as a string or a list of content blocks."""
    final_message = result["messages"][-1]
    content = final_message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)

    return str(content)


def parse_severity(answer: str):
    """Extracts the SEVERITY line the agent is instructed to output first,
    and returns (severity_label, remaining_text)."""
    match = re.match(
        r"\s*SEVERITY:\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\n+(.*)",
        answer,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        severity = match.group(1).upper()
        remaining = match.group(2).strip()
        return severity, remaining
    return "INFO", answer


def render_severity_badge(severity: str):
    css_class = SEVERITY_BADGE_CLASS.get(severity, "cg-badge-info")
    st.markdown(
        f'<span class="cg-badge {css_class}">⚠ {severity}</span>',
        unsafe_allow_html=True,
    )


def run_agent(query: str):
    try:
        result = st.session_state.agent.invoke(
            {"messages": [{"role": "user", "content": query}]}
        )
    except Exception as exc:
        st.error(
            "⚠️ Something went wrong while analyzing this request. "
            "This is usually caused by a network issue or an API problem. "
            f"Details: {exc}"
        )
        return "INFO", None

    raw_answer = extract_answer_text(result)
    severity, clean_answer = parse_severity(raw_answer)
    return severity, clean_answer


def build_pdf(query: str, severity: str, answer: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "CyberGuard AI - Security Advisory Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Severity: {severity}", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Query:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, query.encode("latin-1", "replace").decode("latin-1"))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Advisory:", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, answer.encode("latin-1", "replace").decode("latin-1"))
    return bytes(pdf.output(dest="S"))


def display_report(query: str, severity: str, answer: str, key_prefix: str):
    render_severity_badge(severity)
    st.markdown(f'<div class="cg-card">{answer}</div>', unsafe_allow_html=True)
    pdf_bytes = build_pdf(query, severity, answer)
    st.download_button(
        label="⬇️ Download PDF Report",
        data=pdf_bytes,
        file_name="cyberguard_advisory_report.pdf",
        mime="application/pdf",
        key=f"pdf_{key_prefix}",
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ CyberGuard AI")
    st.markdown(
        "An AI security advisory assistant that analyzes suspicious emails, "
        "alerts, and screenshots using **RAG**, **web search grounding**, "
        "and **OCR**."
    )
    st.markdown("---")
    st.markdown("**Capabilities**")
    st.markdown(
        """
        <span class="cg-badge cg-badge-info">RAG Knowledge Base</span>
        <span class="cg-badge cg-badge-info">Web Search Grounding</span><br><br>
        <span class="cg-badge cg-badge-ok">OCR</span>
        <span class="cg-badge cg-badge-critical">Threat Advisory Agent</span>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("**Session Stats**")

    total = len(st.session_state.history)
    critical_high = sum(
        1 for h in st.session_state.history if h["severity"] in ("CRITICAL", "HIGH")
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div class="cg-stat-box"><div class="cg-stat-num">{total}</div>'
            f'<div class="cg-stat-label">Analyzed</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="cg-stat-box"><div class="cg-stat-num">{critical_high}</div>'
            f'<div class="cg-stat-label">Critical/High</div></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="cg-header">
        <h1>🛡️ CyberGuard AI</h1>
        <p>Security Threat Advisory Assistant — powered by RAG + Agentic Search</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_text, tab_image, tab_history, tab_about = st.tabs(
    ["🔍 Text Query", "📷 Screenshot / Image Analysis", "🕘 History", "ℹ️ About"]
)

with tab_text:
    st.markdown("#### Describe the suspicious email, log, or alert")

    st.markdown("**Quick examples:**")
    example_cols = st.columns(len(EXAMPLE_QUERIES))
    for col, (label, sample_query) in zip(example_cols, EXAMPLE_QUERIES.items()):
        with col:
            st.markdown('<div class="cg-example-btn">', unsafe_allow_html=True)
            if st.button(label, key=f"example_{label}"):
                st.session_state.query_text = sample_query
            st.markdown("</div>", unsafe_allow_html=True)

    query = st.text_area(
        label="query_input",
        label_visibility="collapsed",
        placeholder="e.g. I received an email saying my account will be blocked unless I verify it immediately...",
        height=120,
        key="query_text",
    )

    if st.button("🔎 Analyze", key="analyze_text"):
        if query.strip():
            with st.spinner("Analyzing with RAG + web search..."):
                severity, answer = run_agent(query)
            if answer is not None:
                st.session_state.history.append(
                    {"query": query, "severity": severity, "answer": answer}
                )
                st.markdown("#### 📋 Advisory Report")
                display_report(query, severity, answer, key_prefix="text")
        else:
            st.warning("Please enter a query first.")

with tab_image:
    st.markdown("#### Upload a screenshot (email, alert, or log)")
    uploaded_file = st.file_uploader(
        "upload", type=["png", "jpg", "jpeg"], label_visibility="collapsed"
    )
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded screenshot", width=400)

        if st.button("🔎 Extract & Analyze", key="analyze_image"):
            extracted_text = ""
            try:
                with st.spinner("Running OCR..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    extracted_text = extract_text_from_image(tmp_path)
            except Exception as exc:
                st.error(
                    "⚠️ Could not read text from this image. Make sure Tesseract "
                    f"OCR is installed correctly. Details: {exc}"
                )

            if extracted_text.strip():
                st.markdown("**Extracted text (OCR):**")
                st.markdown(
                    f'<div class="cg-card">{extracted_text}</div>',
                    unsafe_allow_html=True,
                )

                with st.spinner("Analyzing with RAG + web search..."):
                    severity, answer = run_agent(extracted_text)
                if answer is not None:
                    st.session_state.history.append(
                        {
                            "query": f"[Image] {extracted_text[:80]}...",
                            "severity": severity,
                            "answer": answer,
                        }
                    )
                    st.markdown("#### 📋 Advisory Report")
                    display_report(extracted_text, severity, answer, key_prefix="image")
            elif extracted_text == "":
                st.warning(
                    "No readable text was found in this image. Try a clearer "
                    "screenshot."
                )

with tab_history:
    if not st.session_state.history:
        st.info("No queries analyzed yet in this session.")
    else:
        for i, item in enumerate(reversed(st.session_state.history), start=1):
            idx = len(st.session_state.history) - i + 1
            with st.expander(f"Query {idx}  [{item['severity']}] — {item['query'][:50]}..."):
                render_severity_badge(item["severity"])
                st.markdown(f"**Query:** {item['query']}")
                st.markdown(f'<div class="cg-card">{item["answer"]}</div>', unsafe_allow_html=True)

with tab_about:
    st.markdown(
        f"""
        <div class="cg-card">
            <h3>🛡️ CyberGuard AI</h3>
            <p>An AI-powered Security Threat Advisory Assistant built as a final
            project, combining Retrieval-Augmented Generation (RAG), an agentic
            workflow, real-time web search grounding, and OCR to help SOC
            analysts quickly triage suspicious emails, logs, and alerts.</p>
            <hr style="border-color: rgba(148,163,184,0.2);">
            <p><b>Created by:</b> {CREATOR_NAME}</p>
            <p><b>GitHub:</b> <a href="{GITHUB_LINK}" style="color:#7dd3fc;">{GITHUB_LINK}</a></p>
            <p><b>Tech stack:</b> LangChain, LangGraph, Google Gemini, FAISS,
            Tavily Search, Tesseract OCR, Streamlit, LangSmith</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
