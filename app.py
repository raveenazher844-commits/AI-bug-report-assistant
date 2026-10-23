
import streamlit as st
from bug_workflow import generate_bug_report

st.set_page_config(
    page_title="AI Bug Report Assistant",
    page_icon="🐞",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #101827, #18243b, #241d3b);
    color: #f4f6fb;
}
.block-container {
    max-width: 1050px;
    padding-top: 2rem;
}
.hero {
    padding: 28px;
    border-radius: 18px;
    background: linear-gradient(120deg, #253c66, #49346b);
    border: 1px solid #59688c;
    margin-bottom: 24px;
}
.hero h1 {
    color: white;
    margin-bottom: 8px;
}
.hero p {
    color: #e2e8f7;
    font-size: 17px;
}
div.stButton > button {
    background: #7c6cf0;
    color: white;
    border: none;
    border-radius: 10px;
    min-height: 45px;
    font-weight: bold;
    width: 100%;
}
div.stButton > button:hover {
    background: #6555d9;
    color: white;
}
[data-testid="stMetric"] {
    background: #202d45;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #394a68;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🐞 AI Bug Report Assistant</h1>
    <p>
        Turn a simple bug description into a structured report
        using Google Gemini and LangGraph.
    </p>
</div>
""", unsafe_allow_html=True)

st.subheader("📝 Describe Your Bug")

st.write(
    "Explain what happened, what you expected, "
    "and any error message you received."
)

sample_bug = (
    "When users click the Login button with correct credentials, "
    "the page keeps loading and never opens the dashboard. "
    "This happens in Chrome on the latest version of the website."
)

bug_description = st.text_area(
    "Bug Description",
    placeholder="Example: The login page freezes after clicking Login...",
    height=160,
    max_chars=5000
)

with st.expander("💡 View example bug description"):
    st.write(sample_bug)

    if st.button("Use Example"):
        st.session_state["example_bug"] = sample_bug
        st.rerun()

if "example_bug" in st.session_state:
    st.info(
        "Example ready: copy the example above into the "
        "Bug Description box, then click Analyze Bug."
    )

analyze = st.button("🔍 Analyze Bug & Generate Report")

if analyze:
    if not bug_description.strip():
        st.warning("Please enter a bug description first.")
    else:
        try:
            with st.spinner(
                "Gemini is analyzing the bug through 4 workflow nodes..."
            ):
                result = generate_bug_report(bug_description)

            st.success("Bug report generated successfully!")

            st.divider()
            st.subheader("📊 Analysis Results")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Severity", result["severity"])

            with col2:
                st.metric(
                    "Affected Feature",
                    result["affected_feature"]
                )

            st.markdown("### 🏷️ Bug Title")
            st.write(result["title"])

            st.markdown("### 📌 Issue Summary")
            st.write(result["issue_summary"])

            st.markdown("### ⚠️ Severity Reason")
            st.write(result["severity_reason"])

            st.markdown("### 🔎 Possible Root Causes")
            for index, cause in enumerate(
                result["possible_causes"], start=1
            ):
                st.write(f"{index}. {cause}")

            st.divider()
            st.subheader("📄 Complete Bug Report")

            st.markdown(result["formatted_report"])

            st.download_button(
                label="⬇️ Download Bug Report",
                data=result["formatted_report"],
                file_name="bug_report.md",
                mime="text/markdown"
            )

        except Exception as error:
            st.error(
                "The report could not be generated. "
                "Check your API key, model availability, "
                "internet connection, and terminal error."
            )
            st.exception(error)

st.divider()
st.caption(
    "Built with Python • Streamlit • Google Gemini • LangGraph"
)
