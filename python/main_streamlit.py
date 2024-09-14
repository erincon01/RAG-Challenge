import os
import sys
import re
from datetime import datetime
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
import streamlit as st

from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_postgres import load_matches_data_into_postgres_from_folder, load_lineups_data_into_postgres, \
    load_events_data_into_postgres, copy_data_from_postgres_to_azure, download_match_script, \
    get_game_players_data, \
    get_competitions_summary_data, get_matches_summary_data, get_players_summary_data, get_teams_summary_data, get_events_summary_data
from module_azureopenai import get_tokens_statistics_from_table_column, create_events_summary_per_pk_from_json_rows_in_database, \
    create_and_download_detailed_match_summary, create_match_summary, search_details_using_embeddings

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

def connection_button():

    data_source = st.radio(
            "Data source:",
            options=["Azure", "Local"],
            index=0, horizontal=True
        )

    st.session_state.data_source = data_source.lower()

def load_header():

    st.set_page_config(page_title="RAG-Challenge", page_icon="🏠")
    st.title("Sabados Tech - RAG Challenge")

    st.markdown(
        """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:

        selected = option_menu(
            menu_title="Menu",  # 
            options=[
                "The project",
                "Competitions",
                "Matches",
                "Players",
                "Teams",
                "Events",
                "Statistics",
                "Chatbot",
                "Readme"
            ],
            icons=[
                "house", "list-task", "calendar", "person", "people", 
                "list", "bar-chart", "chat-dots", "book"
            ],  # Iconos opcionales
            menu_icon="cast",  # Icono del menú
            default_index=0,  # Índice de la opción por defecto
            orientation="vertical",  # Orientación del menú
            styles={
                "container": {"padding": "5!important", "background-color": "#ffffff"},  # Fondo normal
                "icon": {"color": "black", "font-size": "16px"},  # Color y tamaño de los iconos
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#f0f0f0"},  # Estilos de los enlaces
                "nav-link-selected": {"background-color": "#444444", "color": "white"},  # Estilo de la opción seleccionada
            }        
        )

    icon_mapping = {
        "The project": "house",
        "Competitions": "list-task",
        "Matches": "calendar",
        "Players": "person",
        "Teams": "people",
        "Events": "list",
        "Statistics": "bar-chart",
        "Chatbot": "chat-dots",
        "Readme": "book"
    }

    icon = icon_mapping.get(selected, "house")  # Obtiene el icono del menú seleccionado

    st.markdown(
        f"""
        <h2><i class="bi bi-{icon}" style="margin-right: 8px;"></i>{selected}</h2>
        """,
        unsafe_allow_html=True
    )

    if selected.lower() == "competitions" or selected.lower() == "matches" or \
        selected.lower() == "players" or selected.lower() == "teams" or \
        selected.lower() == "events":

        content = load_file("../statsbomb_data_introduction.md")
        selected_section = extract_section(content, selected.capitalize())
        st.markdown(selected_section)

    return selected

###
### main section / page
###

try:

    load_dotenv(dotenv_path='./../.env')
    selected = load_header()
    menu = selected.lower()

    connection_button()
    source = st.session_state.data_source

    # Show content based on the selected option
    if menu == "the project":

        content = load_file(".//..//README.md")
        section = extract_section(content, "Overview")
        st.markdown(section)

    elif menu == "competitions":

        df = get_competitions_summary_data(source, True)
        df.index = df.index + 1
        st.dataframe(df, width=750)
        
    elif menu == "matches":

        df = get_matches_summary_data(source, True)
        df.index = df.index + 1
        st.dataframe(df, width=750)

    elif menu == "players":

        df = get_players_summary_data(source, True)
        df.index = df.index + 1
        st.dataframe(df, width=750)

    elif menu == "teams":

        df = get_teams_summary_data(source, True)
        df.index = df.index + 1
        st.dataframe(df, width=750)

    elif menu == "events":

        df = get_events_summary_data(source, True)
        df.index = df.index + 1
        st.dataframe(df, width=750)

    elif menu =="statistics":

        s = get_tokens_statistics_from_table_column(source, "events_details", "json_", "", 25000)
        st.markdown("### Data Statistics")
        st.write(s)

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

