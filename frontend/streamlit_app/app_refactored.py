"""
Refactored Streamlit application - Frontend as HTTP client.

This version of the app communicates with the FastAPI backend via HTTP,
following a clean separation between frontend (UI) and backend (business logic).
"""

import streamlit as st
import json
from services.api_client import get_api_client

# Page configuration
st.set_page_config(
    page_title="RAG Challenge - UEFA Euro Analysis",
    page_icon="⚽",
    layout="wide",
)

# Initialize API client
api_client = get_api_client()

# Title
st.title("⚽ RAG Challenge - UEFA Euro Match Analysis")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")

    # Database source selection
    source = st.selectbox(
        "Database Source",
        ["postgres", "sqlserver"],
        help="Select the database to query"
    )

    # Mode selection
    mode = st.radio(
        "Mode",
        ["user mode", "developer mode"],
        help="User mode: simplified interface, Developer mode: advanced options"
    )

    # Advanced settings (developer mode only)
    if mode == "developer mode":
        st.subheader("Advanced Settings")

        search_algorithm = st.selectbox(
            "Search Algorithm",
            ["cosine", "inner_product", "l2_euclidean"],
            help="Vector similarity algorithm"
        )

        embedding_model = st.selectbox(
            "Embedding Model",
            [
                "text-embedding-3-small",
                "text-embedding-ada-002",
                "text-embedding-3-large"
            ],
            help="OpenAI embedding model"
        )

        top_n = st.slider("Top N Results", 1, 50, 10)
        temperature = st.slider("Temperature", 0.0, 2.0, 0.1, 0.1)
        show_logs = st.checkbox("Show Logs", value=False)
    else:
        # Default settings for user mode
        search_algorithm = "cosine"
        embedding_model = "text-embedding-3-small"
        top_n = 10
        temperature = 0.4
        show_logs = False

# Main content
try:
    # Health check
    with st.spinner("Connecting to backend..."):
        health = api_client.health_check()
        st.success(f"✓ Connected to backend (Environment: {health.get('environment', 'unknown')})")

    # Get matches
    with st.spinner("Loading matches..."):
        matches = api_client.get_matches(source=source, limit=100)

    if not matches:
        st.warning("No matches found in the database.")
        st.stop()

    # Match selection
    match_options = [
        f"{m['home_team_name']} ({m['home_score']}) - {m['away_team_name']} ({m['away_score']})"
        for m in matches
    ]

    selected_match_display = st.selectbox(
        "Select a match to analyze:",
        match_options,
        index=0
    )

    # Get selected match ID
    selected_index = match_options.index(selected_match_display)
    selected_match_id = matches[selected_index]["match_id"]

    st.divider()

    # Question input section
    st.subheader("Ask a question about the match")

    # Load sample questions
    try:
        with open("./questions.json", "r") as file:
            questions_data = json.load(file)
        questions_list = ["make a summary of the game"] + [
            item["question"] for item in questions_data
        ]
    except Exception:
        questions_list = ["make a summary of the game"]

    selected_question = st.selectbox(
        "Select a sample question (you can edit it below):",
        questions_list
    )

    question = st.text_area(
        "Your question:",
        value=selected_question,
        height=100,
        help="Ask any question about the match"
    )

    # Language selection
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        language = st.radio(
            "Language",
            ["english", "spanish", "german"],
            horizontal=True
        )

    with col2:
        character = st.radio(
            "Character Style (optional)",
            ["none", "Andrés Montes", "Chiquito de la Calzada"],
            horizontal=True,
            help="Add personality to the response"
        )

    with col3:
        add_match_info = st.radio(
            "Include match info:",
            ["Yes", "No"],
            horizontal=True
        )

    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not question.strip():
            st.error("Please enter a question.")
        else:
            # Build system message based on character selection
            system_message = None
            if character == "Chiquito de la Calzada":
                system_message = """Act like Chiquito de la Calzada, the famous Spanish comedian known for his unique expressions.
Use phrases like '¡No puedo!', '¡Fistro!', '¡Pecador de la pradera!'.
Keep your answer ground in the facts but with his characteristic humor.
If the answer is NONE, start with NONE."""
                temperature = 0.4

            elif character == "Andrés Montes":
                system_message = """Act like Andrés Montes, the legendary Spanish sports commentator.
Use expressions like '¡La vida puede ser maravillosa!', '¡Tiki-taka!', '¡Jugón!'.
Bring energy and passion to your commentary while staying factual.
If the answer is NONE, start with NONE."""
                temperature = 0.4

            # Perform search
            with st.spinner("Searching and generating response..."):
                try:
                    result = api_client.search(
                        match_id=selected_match_id,
                        query=question,
                        source=source,
                        language=language,
                        search_algorithm=search_algorithm,
                        embedding_model=embedding_model,
                        top_n=top_n,
                        temperature=temperature,
                        include_match_info=(add_match_info == "Yes"),
                        system_message=system_message
                    )

                    # Display results
                    st.divider()

                    # Question and answer
                    with st.container(border=True):
                        st.markdown(f"**Question:** {result['question']}")
                        if language != "english":
                            st.markdown(f"**Translated:** {result['normalized_question']}")

                        st.divider()
                        st.markdown("**Answer:**")
                        st.markdown(result['answer'])

                    # Match info (if included)
                    if result.get('match_info'):
                        with st.expander("ℹ️ Match Information", expanded=False):
                            match_info = result['match_info']
                            st.markdown(f"**{match_info['display_name']}**")
                            st.markdown(f"Competition: {match_info['competition']['name']}")
                            st.markdown(f"Date: {match_info['match_date']}")

                    # Search results (developer mode or logs enabled)
                    if show_logs or mode == "developer mode":
                        with st.expander(f"🔍 Search Results ({len(result['search_results'])} events)", expanded=False):
                            for sr in result['search_results']:
                                event = sr['event']
                                st.markdown(
                                    f"**Rank {sr['rank']}** (Score: {sr['similarity_score']:.4f}) - "
                                    f"{event['time_description']}"
                                )
                                if event.get('summary'):
                                    st.caption(event['summary'])
                                st.divider()

                    # Metadata (developer mode only)
                    if mode == "developer mode":
                        with st.expander("📊 Metadata", expanded=False):
                            st.json(result['metadata'])

                except Exception as e:
                    st.error(f"Error during search: {str(e)}")
                    if mode == "developer mode":
                        st.exception(e)

except Exception as e:
    st.error(f"Failed to connect to backend: {str(e)}")
    st.info(f"Make sure the backend is running at: {api_client.base_url}")

    if mode == "developer mode":
        st.exception(e)
