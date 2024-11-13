import os
import sys
import re
from datetime import datetime
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import json as json
import yaml

sys.path.append(os.path.abspath('./python_modules'))

from module_data import get_games_with_embeddings
from module_azure_openai import search_details_using_embeddings
from module_streamlit_frontend import load_file, extract_section, \
    menu_about_us, menu_competitions, menu_matches, menu_teams, menu_tables_information, menu_project, \
    menu_players, menu_events, menu_chatbot_logs, menu_readme


def call_gpt(source):

    # Define default values

    input_tokens = int(50000 * 1/2)
    output_tokens = int(5000 * 1/3)

    selected_embeddings_model = "text-embedding-ada-002"
    selected_search_type = "Cosine"

    temperature = 0.25
    top_n = 10

    selected_show_logs = "No"
    selected_add_match_info = "Yes"

    ###### England - Spain match_id: 3943043  
    match_id = 3943043
    add_match_info = "Yes"

    system_message = f"""Answer the users QUESTION using the EVENTS or GAME_RESULT listed above.
Keep your answer ground in the facts of the EVENTS or GAME_RESULT.
If the EVENTS or GAME_RESULT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question. """   

    selected_question = ""
    mode = st.session_state.mode
    selected_mini_tune = "yes"

    games_df = get_games_with_embeddings(source, as_data_frame=True)

    if mode == "developer mode":

        with st.container(border=True):    
            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)
            col5, col6 = st.columns(2)
            col7, col8 = st.columns(2)

        # Slider for input_tokens in the first column
        with col1:
            input_min = 10000  # 10K
            input_max = 50000  # 50K
            input_tokens = st.slider("Input Tokens", min_value=input_min, max_value=input_max, value=int(input_max * 1/2), step=1000)

        # Slider for output_tokens in the second column

        with col2:
            output_min = 500  # 500
            output_max = 2500  # 2500
            output_tokens = st.slider("Output Tokens", min_value=output_min, max_value=output_max, value=int(output_max*1/3), step=100)

        # Define the two options
        selected_embeddings_model=""
        if (source.lower() == "azure-postgres"):
            with col3:
                model = ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large", "multilingual-e5-small:v1"]
                selected_embeddings_model = st.radio("Choose a model", model)

        if (source.lower() == "azure-sql"):
            with col3:
                model = ["text-embedding-ada-002", "text-embedding-3-small"]
                selected_embeddings_model = st.radio("Choose a model", model)

        selected_search_type=""
        selected_add_match_info=""
        if (source.lower() == "azure-postgres"):
            with col4:
                search_type = ["Cosine", "Negative Inner Product", "L1", "L2"]
                selected_search_type = st.radio("Choose a search type", search_type).lower()

        if (source.lower() == "azure-sql"):
            with col4:
                search_type = ["Cosine", "Negative Inner Product", "L2"]
                selected_search_type = st.radio("Choose a search type", search_type).lower()

        with col5:
            temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.25, step=0.01)

        with col6:
            top_n = st.slider("Top n results", min_value=5, max_value=50, value=10, step=5)

        with col7:
            show_logs = ["Yes", "No"]
            selected_show_logs = st.radio("Show logs", show_logs, index=1)   

        with col8:
            add_match_info = ["Yes", "No"]
            selected_add_match_info = st.radio("Include match info in search:", add_match_info)    

    questions_list = ["make a summary of the game"]
    try:
        # Try to open and load the JSON file
        with open("./questions.json", "r") as file:
            questions_data = json.load(file)
        questions_list += [item["question"] for item in questions_data]        
    except Exception as e2:
        questions_list = [e2.args]

    add_match_info = selected_add_match_info.lower()
    match_id = 3943043 ###### England - Spain match_id: 3943043  

    system_message = f"""Answer the users QUESTION using the EVENTS or GAME_RESULT listed above.
Keep your answer ground in the facts of the EVENTS or GAME_RESULT.
If the EVENTS or GAME_RESULT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question. """   

    if not games_df.empty:
        # Crear una lista de opciones para el selectbox usando los nombres de los equipos y el ID del partido
        game_options = [f"{row['home_team_name']} ({row['home_score']}) - {row['away_team_name']} ({row['away_score']})" for _, row in games_df.iterrows()]
        selected_game = st.selectbox("Select game to analyze:", game_options)

        # get the match_id from the selected game
        selected_game_id = next((row['match_id'] for _, row in games_df.iterrows() if f"{row['home_team_name']} ({row['home_score']}) - {row['away_team_name']} ({row['away_score']})" == selected_game), 3943043)
        match_id = selected_game_id

    if mode == "developer mode":
        # Display the text box that allows editing the system message
        system_message = st.text_area("Role.system / System Message:", value=system_message, height=125)
    
    selected_question = st.selectbox("Select a sample question:  [you can edit the question in the text area below]", questions_list)

    if selected_question =="":
        selected_question = "make a summary of the game"
    text_question = st.text_area("Edit your question here:", value=selected_question, height=125)

    language = ["English", "Spanish", "German"]
    selected_language = st.radio("Choose a language", language, horizontal=True).lower()

    selected_parody = "none"
    parody = ["none", "Andrés Montes", "Chiquito de la Calzada"]
    selected_parody = st.radio("Choose a parody", parody, horizontal=True)
    if selected_parody == "Chiquito de la Calzada":
        selected_parody = "Chiquito"

    if mode == "developer mode":

        mini_tune = ["No", "Yes"]
        selected_mini_tune = st.radio("Enable mini tune", mini_tune, horizontal=True).lower()

    if st.button("Search"):
        question = text_question
        system_message += " Please, make sure that the ANSWER is in " + selected_language.upper() + "."

        if selected_parody == "Chiquito" or selected_parody == "Andrés Montes":
            system_message += f"Emulate the style of a well-known humorous character, such as [" + selected_parody + f"].\n"
            system_message += f"Incorporate the humor, expressions, and well-known catchphrases of the character in your answer.\n"
            system_message += f"Below is a list of five of his most popular phrases and the context in which he would use them.\n"
            system_message += f"DO NOT start the RESPONSE with ANY OF THESE phrases. The phrase is in Spanish, and the explanation is in English in this format [ ### phrase ### - explanation ]. Use it ONLY TWO TIMES in IMPORTANT game actions.\n"

            if selected_parody == "Chiquito":
                system_message += f"[### ¡Fistro! ### - This word was often used by Chiquito as an exclamation, similar to 'Wow!' in English. He would use it to express surprise or amazement]\n"
                system_message += f"[###  ¿Te da cuen? ### - This phrase translates loosely to 'You get it?']\n"
                system_message += f"[###  Jarl! ### - Used to show a sudden reaction of shock, confusion, or mild fear, similar to saying 'Oh my!' or 'Goodness!' in English]\n"
                system_message += f"[###  Pecador de la pradera ### - Used this phrase to humorously accuse someone of mischievousness or wrongdoing, but in a lighthearted way]\n"
                system_message += f"[###  Hasta luego, Lucas ### - This playful farewell translates to 'See you later'. Often at the end of a joke or scene, giving a comedic endnote to his skits]\n"
                system_message += f"Keep these expressions and tones in mind to emulate Chiquito de la Calzada's signature humor and unique style in responses.\n"

            if selected_parody == "Andrés Montes":
                system_message += f"[###  '¡La vida puede ser maravillosa!' ### - This phrase, meaning 'Life can be wonderful!' in English, used by Montes to celebrate moments of joy or impressive plays]\n"
                system_message += f"[###  '¡Tiki-taka!' ### - Describe the quick, short passing style in football, to highlight the beauty of coordinated teamwork and skillful ball movement]\n"
                system_message += f"[###  '¡Jugón!' ### - Describe players with exceptional skill and flair. It loosely translates to 'superstar' or 'player with great flair']\n"
                system_message += f"[###  '¿Dónde están las llaves, Salinas?' ### - This playful question, 'Where are the keys, Salinas?' was often directed humorously in moments of confusion or disbelief]\n"
                system_message += f"[###  '¡Ratatatatatatatá!' ### - Used for  intense, rapid sequences in basketball or football, mimicking the sound of machine-gun fire to emphasize the high pace and excitement]\n"
                system_message += f"Keep these expressions and tones to emulate Andrés Montes dynamic, enthusiastic style in mind to bring his iconic flair to responses.\n"

            system_message += f"Act like him. DO NOT say you are performing like him.\n"
            system_message += f"If the answer is NONE it is IMPORTANT to start the response with NONE.\n"
            temperature = 0.40

        if selected_mini_tune == "yes" or mode == "user mode":

            search_algorithms = ""
            if source == "azure-postgres":
                search_algorithms = ["Cosine", "Negative Inner Product", "L1", "L2"]
            if source == "azure-sql":
                search_algorithms = ["Cosine", "Negative Inner Product", "L2"]

            # for each search algorithm
            for algorithm in search_algorithms:
                selected_search_type = algorithm
                if mode == "user mode":
                    st.write("Searching with algorithm #" + str(search_algorithms.index(algorithm)+1) +  "...")
                else:
                    st.write("Searching with " + selected_search_type + " algorithm...")
                dataset, result = search_details_using_embeddings (source, match_id, add_match_info, \
                                    selected_language, selected_search_type, selected_embeddings_model, \
                                    system_message, question, top_n, temperature, input_tokens, output_tokens)

                # if response don't start with "NONE" finish the loop
                if not result.startswith("NONE"):
                    break
                
        else:
            result = search_details_using_embeddings (source, match_id, add_match_info, \
                                    selected_language, selected_search_type, selected_embeddings_model, \
                                    system_message, question, top_n, temperature, input_tokens, output_tokens)
        
        with st.container(border=True):
                if language != "english":
                    st.write(f"Question [{question}] translated to English.")
                st.markdown(result)

        # # Cargar y reproducir el audio
        # with open(filename, "rb") as audio_file:
        #     st.audio(audio_file.read(), format="audio/wav")                

        if selected_show_logs == "Yes":
            with st.container(border=True, height=250):
                    st.markdown(dataset)


def connection_button(menu):

    mode = "user mode"
    data_source = "azure-sql"

    if menu.lower()== "chatbot":
        mode = st.radio("Select mode:", ("User mode", "Developer mode"), horizontal=True)
        if mode == "Developer mode":
            data_source = st.radio(
                    "Data source:",
                    options=["Azure-Postgres", "Azure-SQL"],
                    index=1, horizontal=True
                )
    else:
        if menu.lower()== "events" or menu.lower() == "tables information":
            data_source = st.radio(
                    "Data source:",
                    options=["Azure-Postgres", "Azure-SQL"],
                    index=1, horizontal=True
                )
        else:
            data_source = st.radio(
                    "Data source:",
                    options=["Azure-Postgres", "Azure-SQL", "sqlite-Local"],
                    index=1, horizontal=True
                )

    st.session_state.mode = mode.lower()
    st.session_state.data_source = data_source.lower()

def load_menu():

    st.set_page_config(page_title="Football Analytics Copilot", page_icon="🏠")
    st.title("Football Analytics Copilot")

    st.markdown(
        """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:

        selected = option_menu(
            menu_title="Menu",
            options=[
                "Chatbot",
                "Chatbot logs",
                "The project",
                "Readme",
                "Tables Information",
                "Competitions",
                "Matches",
                "Teams",
                "Players",
                "Events",
                "About Us"
            ],
            icons=[
                "chat-dots", "bar-chart", "house", "book", "list-task", "database", "calendar", "people", "person",
                "list", "book"
            ],  # Optional icons
            menu_icon="cast",  # Menu icon
            default_index=0,  # Default option index
            orientation="vertical",  # Menu orientation
            styles={
                ## "container": {"padding": "5!important", "background-color": "#ffffff"},  # Normal background
                "icon": {"color": "black", "font-size": "16px"},  # Icon color and size
                ## "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#f0f0f0"},  # Link styles
                ## "nav-link-selected": {"background-color": "#444444", "color": "white"},  # Selected option style
            }        
        )

    icon_mapping = {
        "Chatbot": "chat-dots",
        "Chatbot logs": "bar-chart",
        "The project": "house",
        "Readme": "book",
        "Competitions": "list-task",
        "Matches": "calendar",
        "Players": "person",
        "Teams": "people",
        "Events": "list",
        "Tables Information": "database",
        "About Us": "book"
    }

    icon = icon_mapping.get(selected, "house")  # Get the icon of the selected menu

    st.markdown(
        f"""
        <h2><i class="bi bi-{icon}" style="margin-right: 8px;"></i>{selected}</h2>
        """,
        unsafe_allow_html=True
    )

    if selected.lower() == "competitions" or selected.lower() == "matches" or \
        selected.lower() == "players" or selected.lower() == "teams" or \
        selected.lower() == "events" or selected.lower() == "tables information":

        content = load_file("./docs/statsbomb-intro.md")
        selected_section = extract_section(content, selected.capitalize())
        st.markdown(selected_section)

    return selected


###  app.py entry point

try:

    load_dotenv(dotenv_path='././.env')
    module_path = os.path.abspath(os.path.join("python"))
    sys.path.append(module_path)
    selected = load_menu()
    menu = selected.lower()

    if menu != "the project" and menu != "chatbot logs" and menu != "readme" and menu != "about us":
        connection_button(menu)
        source = st.session_state.data_source

    # Show content based on the selected option
    if menu == "the project":
        with st.container(border=True):
            menu_project("./docs/project.md")

    elif menu == "about us":
        with st.container(border=True):
            menu_about_us()

    elif menu == "tables information":
        with st.container(border=True):
            menu_tables_information(source)

    elif menu == "competitions":
        with st.container(border=True):
            menu_competitions(source)

    elif menu == "matches":
        with st.container(border=True):
            menu_matches(source)

    elif menu == "teams":
        with st.container(border=True):
            menu_teams(source)
         
    elif menu == "players":
        with st.container(border=True):
            menu_players(source)

    elif menu == "events":
        with st.container(border=True):
            menu_events(source)

    elif menu =="chatbot logs":
        with st.container(border=True):
            menu_chatbot_logs()

    elif menu == "chatbot":
        with st.container(border=True):
            call_gpt(source)

    elif menu == "readme":
        with st.container(border=True):
            menu_readme("./docs/project.md")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
