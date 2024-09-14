import os
import sys
import re
from datetime import datetime
from dotenv import load_dotenv

from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_postgres import load_matches_data_into_postgres_from_folder, load_lineups_data_into_postgres, \
    load_events_data_into_postgres, copy_data_from_postgres_to_azure, download_match_script, \
    get_game_players_data, get_competitions_summary_data, get_matches_summary_data
from module_azureopenai import get_tokens_statistics_from_table_column, create_events_summary_per_pk_from_json_rows_in_database, \
    create_and_download_detailed_match_summary, create_match_summary, search_details_using_embeddings

import streamlit as st

def load_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
    return content

def extract_headers(content):
    # Regular expression to find headers
    headers = re.findall(r'^(#+)\s+(.*)', content, re.MULTILINE)
    toc = []
    for header in headers:
        level = len(header[0])  # Header level
        text = header[1]        # Header text
        link = text.lower().replace(' ', '-')  # Create an ID for the header
        toc.append((level, text, link))
    return toc

def generate_toc(toc, levels):
    toc_html = '<ul>'
    for level, text, link in toc:
        if level == 1 and level <= levels:
            toc_html += f'<li><a href="#{link}">{text}</a>'
        elif level == 2 and level <= levels:
            toc_html += f'<ul><li><a href="#{link}">{text}</a></li></ul>'
        elif level == 3 and level <= levels:
            toc_html += f'<ul><ul><li><a href="#{link}">{text}</a></li></ul></ul>'
    toc_html += '</ul>'
    return toc_html

def extract_section(content, section_title):
    # Define regex pattern to match the desired section
    pattern = re.compile(rf'## {re.escape(section_title)}(.*?)(?=## |$)', re.DOTALL)
    
    # Find the section matching the pattern
    match = pattern.search(content)
    
    if match:
        return match.group(1).strip()
    return "Section not found."

###
### main section / page
###

load_dotenv(dotenv_path='./../.env')
st.set_page_config(page_title="RAG-Challenge", page_icon="🏠")
st.title("Sabados Tech - RAG Challenge")

# Create the menu in the sidebar
menu = st.sidebar.radio(
    "Menu",
    ["Start", "Competitions", "Matches", "Players", "Teams", "Events", "Statistics", "Chatbot", "Readme"]
)

menu = menu.lower()

try:

    # Show content based on the selected option
    if menu == "start":
        st.subheader("💬 Overview")
        content = load_file(".//..//README.md")

        section = extract_section(content, "Overview")
        st.markdown(section)

    elif menu == "competitions":
        st.subheader("Competitions")
        df = get_competitions_summary_data("azure", True)
        st.dataframe(df)

    elif menu == "matches":
        st.subheader("Matches")
        df = get_matches_summary_data("azure", True)
        st.dataframe(df)

    elif menu == "players":
        df = get_game_players_data("azure", 3943043, True)
        st.markdown("### Players")
        st.dataframe(df)

    elif menu == "teams":
        df = get_game_players_data("azure", 3943043, True)
        st.markdown("### Players")
        st.dataframe(df)

    elif menu == "events":
        df = get_game_players_data("azure", 3943043, True)
        st.markdown("### Players")
        st.dataframe(df)

    elif menu =="statistics":

        st.title("Statistics")
        s = get_tokens_statistics_from_table_column('azure', "events_details__quarter_minute", "json_", "match_id = 3943043", -1)
        st.markdown("### Data Statistics")
        st.dataframe(s)

    elif menu == "chatbot":

        value = st.text_input("Enter a value:")
        st.write("The entered value is:", value)

        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input():
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

    elif menu == "readme":
        content = load_file("../README.md")

        # Extract headers and generate TOC
        toc = extract_headers(content)
        toc_html = generate_toc(toc, 2)

        # Show TOC and Markdown content
        st.markdown(f'<div style="margin-bottom: 20px;">{toc_html}</div>', unsafe_allow_html=True)
        st.markdown(content)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")

