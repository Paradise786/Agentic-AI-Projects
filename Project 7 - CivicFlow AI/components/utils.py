import streamlit as st
import json

def json_to_cards(data: dict) -> None:
    """Render the AI case intelligence card UI.
    Expects a dict with a top‑level ``super_agent`` key containing the
    ``selected_agents`` list and additional metadata (case ID, status, confidence, etc.).
    This function hides the raw JSON and instead displays a formatted Card with a
    button that expands to show the full reasoning timeline.
    """
    # Extract basic fields – fallback values if missing
    case_id = data.get('case_id', data.get('ticket_id', 'UNKNOWN'))
    status = data.get('status', 'Pending')
    confidence = data.get('confidence', data.get('ai_confidence', 0))
    # Build the header markdown
    header_md = f"""
    ### 🧠 AI Case Intelligence

    **Case:** {case_id}
    **Status:** {status}
    **AI Confidence:** {confidence}%
    """
    st.markdown(header_md)
    # Build the progress line (static example – replace with real steps if available)
    steps = ["Understand Issue", "Verify Evidence", "Check Memory", "Detect Duplicates", "Calculate Risk", "Route Department"]
    step_md = " → ".join([f"`{s}` ✓" for s in steps])
    st.markdown(step_md)
    # Button to show full JSON (or detailed timeline)
    with st.expander("**View Full AI Reasoning**"):
        st.code(json.dumps(data, indent=2), language="json")
