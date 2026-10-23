
import os
import json
from typing import TypedDict, List

from dotenv import load_dotenv
from google import genai
from langgraph.graph import StateGraph, START, END

# Load API key and model settings from .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY missing. Please add it to your .env file."
    )

client = genai.Client(api_key=API_KEY)


# Shared state used by all four LangGraph nodes
class BugState(TypedDict, total=False):
    bug_description: str
    title: str
    affected_feature: str
    issue_summary: str
    severity: str
    severity_reason: str
    possible_causes: List[str]
    formatted_report: str


# Helper function: ask Gemini for a response
def ask_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()


# Helper function: convert Gemini JSON into a Python dictionary
def ask_gemini_json(prompt: str) -> dict:
    response_text = ask_gemini(
        prompt
        + "\n\nReturn only a valid JSON object. "
          "Do not include Markdown code fences."
    )

    # Handle accidental Markdown code fences
    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "", 1)
        response_text = response_text.replace("```", "").strip()

    return json.loads(response_text)


# NODE 1: Analyze the bug
def bug_analysis(state: BugState) -> dict:
    prompt = f"""
    Analyze this software bug report.

    Bug description:
    {state['bug_description']}

    Extract:
    1. A short, clear bug title
    2. The affected feature or component
    3. A concise issue summary

    Do not invent facts that are not in the description.

    Return JSON with these keys:
    title, affected_feature, issue_summary
    """

    result = ask_gemini_json(prompt)

    return {
        "title": result["title"],
        "affected_feature": result["affected_feature"],
        "issue_summary": result["issue_summary"]
    }


# NODE 2: Detect severity
def severity_detection(state: BugState) -> dict:
    prompt = f"""
    Classify the severity of this software bug.

    Original description: {state['bug_description']}
    Title: {state['title']}
    Affected feature: {state['affected_feature']}
    Summary: {state['issue_summary']}

    Choose exactly one severity:
    Critical, High, Medium, or Low.

    Critical: widespread outage, data loss, security breach,
    or a core system that is unusable.
    High: a major feature is broken with serious impact.
    Medium: a feature is impaired but a workaround may exist.
    Low: minor inconvenience or cosmetic issue.

    Do not assume impact that has not been established.
    Return JSON with keys: severity, severity_reason
    """

    result = ask_gemini_json(prompt)

    severity = result["severity"].strip().title()
    allowed = {"Critical", "High", "Medium", "Low"}

    if severity not in allowed:
        severity = "Medium"

    return {
        "severity": severity,
        "severity_reason": result["severity_reason"]
    }


# NODE 3: Suggest possible root causes
def root_cause_suggestion(state: BugState) -> dict:
    prompt = f"""
    Suggest 3 plausible technical causes for this bug.

    Bug description: {state['bug_description']}
    Title: {state['title']}
    Affected feature: {state['affected_feature']}
    Summary: {state['issue_summary']}
    Severity: {state['severity']}

    Return JSON with one key, possible_causes,
    containing a list of 3 concise explanations.

    These are hypotheses, not confirmed causes.
    Do not claim that you inspected the actual source code.
    """

    result = ask_gemini_json(prompt)

    causes = result.get("possible_causes", [])

    if not isinstance(causes, list):
        causes = [str(causes)]

    return {
        "possible_causes": [str(cause) for cause in causes]
    }


# NODE 4: Format the final bug report
def format_report(state: BugState) -> dict:
    causes = "\n".join(
        f"- {cause}" for cause in state["possible_causes"]
    )

    prompt = f"""
    Format the following analyzed bug into a professional,
    readable Markdown bug report.

    Bug title: {state['title']}
    Affected feature: {state['affected_feature']}
    Original description: {state['bug_description']}
    Issue summary: {state['issue_summary']}
    Severity: {state['severity']}
    Severity reason: {state['severity_reason']}
    Possible root causes:
    {causes}

    Include these sections:
    # Bug Report
    ## Title
    ## Affected Feature
    ## Original Description
    ## Issue Summary
    ## Severity
    ## Severity Reason
    ## Possible Root Causes
    ## Recommended Next Steps

    In Recommended Next Steps, suggest practical investigation
    steps without pretending the bug has been fixed.
    Label possible causes as unconfirmed hypotheses.
    """

    report = ask_gemini(prompt)

    return {"formatted_report": report}


# Build the LangGraph workflow
graph_builder = StateGraph(BugState)

graph_builder.add_node("bug_analysis", bug_analysis)
graph_builder.add_node("severity_detection", severity_detection)
graph_builder.add_node("root_cause_suggestion", root_cause_suggestion)
graph_builder.add_node("format_report", format_report)

graph_builder.add_edge(START, "bug_analysis")
graph_builder.add_edge("bug_analysis", "severity_detection")
graph_builder.add_edge("severity_detection", "root_cause_suggestion")
graph_builder.add_edge("root_cause_suggestion", "format_report")
graph_builder.add_edge("format_report", END)

bug_graph = graph_builder.compile()


# Function called by the Streamlit application
def generate_bug_report(bug_description: str) -> dict:
    initial_state: BugState = {
        "bug_description": bug_description.strip()
    }

    return bug_graph.invoke(initial_state)
