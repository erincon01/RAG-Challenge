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

sys.path.append(os.path.abspath('./python_modules'))

# from module_github import download_data_from_github_repo, get_github_data_from_matches
from  module_data import get_competitions_summary_data, get_competitions_summary_with_teams_data, get_competitions_results_data,\
    get_all_matches_data, get_players_summary_data, get_teams_summary_data, get_events_summary_data, \
    get_competitions_summary_with_teams_and_season_data, get_tables_info_data
from module_azure_openai import search_details_using_embeddings


def process_markdown_with_images(markdown_content):
    # Dividir el contenido por líneas para procesarlo más fácilmente
    lines = markdown_content.split('\n')

    # Patrón para detectar enlaces tipo [texto](enlace.png, .jpg, .jpeg, .gif, etc.)
    pattern_image = r'\[([^\]]+)\]\(([^)]+\.(png|jpg|jpeg|gif))\)'

    # Procesar cada línea
    for line in lines:
        # Buscar si la línea contiene un enlace a una imagen
        match_image = re.search(pattern_image, line, re.IGNORECASE)

        if match_image:
            # Extraer el texto alternativo y el enlace de la imagen
            alt_text = match_image.group(1)
            image_link = match_image.group(2)

            # Mostrar la imagen usando st.image
            st.image(image_link, caption=alt_text)
        else:
            # Si no es una imagen, mostrarlo como markdown
            st.markdown(line, unsafe_allow_html=True)
            

def show_md_contain(file_path, process_images=False):
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    if process_images:
        process_markdown_with_images(markdown_content)
    else:
        st.markdown(markdown_content, unsafe_allow_html=True)


def load_and_process_hrefs(file_path, process_images=False):
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    # Split the content of the file into lines
    lines = markdown_content.splitlines()

    options = []
    links = []

    # Iterate over each line to search and process links and/or images
    for line in lines:
        # Search for links that start with "ST:"
        pattern_link = r'\[ST: ([^\]]+)\]\(([^)]+)\)'
        match_link = re.search(pattern_link, line)

        if match_link:
            title = match_link.group(1)
            link = match_link.group(2)

            # Add title and link to the lists
            options.append(title)
            links.append(link)

    # Mostrar el selectbox con los títulos
    selected_title = st.selectbox('Selecciona un documento:', options)

    # Mostrar el contenido del enlace correspondiente
    if selected_title:
        # Buscar el link asociado al título seleccionado
        selected_link = links[options.index(selected_title)]

        # if selected_tittle starts with "H" then it is a hyperlink
        if selected_title.lower() == "application screenshots":
            show_md_contain(selected_link, True)
        else:
            show_md_contain(selected_link, False)       


def normalize(value, min_value, max_value):
    return (value - min_value) / (max_value - min_value)

def call_gpt(source):

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
    selected_model=""
    if (source.lower() == "azure-postgres"):
        with col3:
            model = ["text-embedding-3-large", "text-embedding-3-small", "multilingual-e5-small:v1", "text-embedding-ada-002"]
            selected_model = st.radio("Choose a model", model)

    if (source.lower() == "azure-sql"):
        with col3:
            model = ["text-embedding-3-small", "text-embedding-ada-002"]
            selected_model = st.radio("Choose a model", model)

    if (source.lower() == "sqlite-local"):
        with col3:
            model = ["text-embedding-3-large", "text-embedding-3-small", "multilingual-e5-small:v1", "text-embedding-ada-002"]
            selected_model = st.radio("Choose a model", model)


    selected_search_type=""
    selected_add_match_info=""
    if (source.lower() == "azure-postgres"):
        with col4:
            search_type = ["Cosine", "Negative Inner Product", "L1", "L2"]
            selected_search_type = st.radio("Choose a search type", search_type)

    if (source.lower() == "azure-sql"):
        with col4:
            search_type = ["Cosine", "Negative Inner Product", "L2"]
            selected_search_type = st.radio("Choose a search type", search_type)

    if (source.lower() == "sqlite-local"):
        with col4:
            search_type = ["Cosine", "Negative Inner Product", "L1", "L2"]
            selected_search_type = st.radio("Choose a search type", search_type)

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

    ###### England - Spain match_id: 3943043  
    match_id = 3943043
    add_match_info = selected_add_match_info.lower()

    system_message = f"""\n\n\nAnswer the users QUESTION using the EVENTS or GAME_RESULT listed above.
        Keep your answer ground in the facts of the EVENTS or GAME_RESULT.
        If the EVENTS or GAME_RESULT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question. """   

    questions_list = []
    try:
        # Try to open and load the JSON file
        with open("./questions.json", "r") as file:
            questions_data = json.load(file)
        questions_list = [item["question"] for item in questions_data]
    except Exception as e2:
        questions_list = [e2.args]

    with st.container(border=True):
        # Display the text box that allows editing the system message
        system_message = st.text_area("Role.system / System Message:", value=system_message, height=125)
        selected_question = st.selectbox("Select a sample question:     ** you can edit the question in the textbox below", questions_list)
        text_question = st.text_area("Edit your question here:", value=selected_question, height=125)

        if st.button("Search"):
            question = text_question

            dataset, result = search_details_using_embeddings (source, match_id, add_match_info, \
                                    selected_search_type, selected_model, \
                                    system_message, question, top_n, temperature, input_tokens, output_tokens)

            with st.container(border=True):
                    st.markdown(result)

            if selected_show_logs == "Yes":
                with st.container(border=True, height=250):
                        st.markdown(dataset)

def parse_sections(content):
    sections = {}
    current_section = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('## '):  # Level 2 sections
            current_section = line[3:].strip()  # Remove the "## " to get the section name
            sections[current_section] = {"content": "", "subsections": {}}  # Initialize the section
            current_subsection = None  # Reset the subsection
        elif line.startswith('### ') and current_section:  # Level 3 sections
            current_subsection = line[4:].strip()  # Remove the "### " to get the subsection name
            sections[current_section]["subsections"][current_subsection] = ""  # Initialize the subsection
        elif current_subsection:  # If we are in a subsection
            sections[current_section]["subsections"][current_subsection] += line + "\n"
        elif current_section:  # If we are in a level 2 section
            sections[current_section]["content"] += line + "\n"
    return sections

def result_to_score_difference(result):
    if pd.isna(result):
        return None
    try:
        score1, score2 = map(int, result.split('-'))
        return score1 - score2
    except ValueError:
        return None
    
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
        elif level == 4 and level <= levels:
            toc_html += f'<ul><ul><ul><li><a href="#{link}">{text}</a></li></ul></ul></ul>'
    toc_html += '</ul>'
    return toc_html

def extract_section(content, section_title):
    """
    Extracts the content of a specified section from a Markdown document.

    Parameters:
    content (str): The Markdown content as a string.
    section_title (str): The title of the section to extract.

    Returns:
    str: The content of the section if found, otherwise "Section not found."
    """
    # Define regex pattern to match the desired section, handling both level 2 and level 3 headers
    pattern = re.compile(rf'## {re.escape(section_title)}(.*?)(?=## |### |$)', re.DOTALL)
    
    # Find the section matching the pattern
    match = pattern.search(content)
    
    if match:
        return match.group(1).strip()
    return "Section not found."

def connection_button(menu):

    if menu.lower()== "events" or menu.lower() == "tables information" or menu.lower() == "chatbot":

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

    st.session_state.data_source = data_source.lower()

def load_header():

    st.set_page_config(page_title="RAG-Challenge", page_icon="🏠")
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
                "The project",
                "Chatbot",
                "Chatbot logs",
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
                "house", "chat-dots", "bar-chart", "book", "list-task", "database", "calendar", "people", "person",
                "list", "book"
            ],  # Optional icons
            menu_icon="cast",  # Menu icon
            default_index=0,  # Default option index
            orientation="vertical",  # Menu orientation
            styles={
                "container": {"padding": "5!important", "background-color": "#ffffff"},  # Normal background
                "icon": {"color": "black", "font-size": "16px"},  # Icon color and size
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#f0f0f0"},  # Link styles
                "nav-link-selected": {"background-color": "#444444", "color": "white"},  # Selected option style
            }        
        )

    icon_mapping = {
        "The project": "house",
        "Chatbot": "chat-dots",
        "Chatbot logs": "bar-chart",
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

        content = load_file("./README-statsbomb-intro.md")
        selected_section = extract_section(content, selected.capitalize())
        st.markdown(selected_section)

    return selected

try:

    load_dotenv(dotenv_path='././.env')
    module_path = os.path.abspath(os.path.join("python"))
    sys.path.append(module_path)
    selected = load_header()
    menu = selected.lower()

    if menu != "the project" and menu != "chatbot logs" and menu != "readme" and menu != "about us":
        connection_button(menu)
        source = st.session_state.data_source

    # Show content based on the selected option
    if menu == "the project":


        filename = "./README-project.md"

        # create the page TOC
        content = load_file(filename)
        toc = extract_headers(content)
        toc_html = generate_toc(toc, 2)
        st.markdown(f'<div style="margin-bottom: 20px;">{toc_html}</div>', unsafe_allow_html=True)

        st.video(".//.//RAG-Challenge_Sabados_Tech.mp4")
        # insert video
        st.markdown("""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        """, unsafe_allow_html=True)

        # Display the football icon
        st.markdown('<h2>Spain <i class="fa fa-futbol-o"></i><i class="fa fa-futbol-o"></i> - England <i class="fa fa-futbol-o"></i></h2>', unsafe_allow_html=True)

        st.video("https://www.youtube.com/watch?v=sQ6rgX77tB0")

        # load md and replace the hrefs with buttons for streamlit
        load_and_process_hrefs(filename, False)

    elif menu == "about us":


        with st.container(border=True):

            st.markdown("##### 🌐Virtual Community of Developers and Technology Enthusiasts")
            texto = """
            **Sábados Tech** is a space created for software developers, engineers, makers, and technology enthusiasts. Every Saturday, we meet virtually to explore and learn about a wide range of technological topics, from programming languages and frameworks to emerging trends in artificial intelligence, cybersecurity, IoT, and much more! There’s always something new to discover. 🚀\n\n
            In our group, the topics for each session are proposed by the members themselves, ensuring that everyone's interests are considered and that the discussions are dynamic and useful. If you have a technical curiosity, a project you want to showcase, or simply want to learn something new, **Sábados Tech** is the perfect place to share with a community of curious minds eager to collaborate. 🤓\n\n
            Would you like to join? We would love for you to be part of our meetings. Join our WhatsApp group to stay up to date with the upcoming topics and schedules:\n\n
            📲 [https://chat.whatsapp.com/L8dj4wxpHUICww7rfeJx8K](https://chat.whatsapp.com/L8dj4wxpHUICww7rfeJx8K)\n\n
            We look forward to seeing you! 👋\n\n
            **Note:** The group speaks in Spanish
            """
            st.markdown(texto)

            st.markdown("##### ⚒️RAG Challenge Leaders")

            st.write("[Eugenio Serrano](https://www.linkedin.com/in/eugenio-serrano/)")
            st.markdown("[Mariano Álvarez](https://www.linkedin.com/in/josemarianoalvarez/)")
            st.markdown("[Eladio Rincón](https://www.linkedin.com/in/erincon/)")


    elif menu == "tables information":

        try:
            df = get_tables_info_data(source, True)
            st.markdown("#### Tables Space Summary")
            st.dataframe(df)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    elif menu == "competitions":

        sum_matches = 0
        avg_matches = 0
        competitions = 0
        num_teams = 0
        num_seasons = 0

        try:            
            df = get_competitions_summary_data(source, True)
            df0 = get_competitions_summary_with_teams_and_season_data(source, True)
            df2 = get_competitions_summary_with_teams_data(source, True)
            df3 = get_competitions_results_data(source, True)

            df.index = df.index + 1
            sum_matches = df["matches_count"].sum()
            avg_matches = df["matches_count"].mean()
            avg_matches = float("{:.2f}".format(avg_matches))
            competitions = len(df)
            num_teams = df2["team_name"].nunique()
            num_seasons = df0["season_name"].nunique()
            st.markdown("### Football Match Data Analysis")

            with st.container(border=True):
                st.write("Competitions: ", competitions, "Matches:", sum_matches, \
                         "Matches/competition:", avg_matches, \
                         "Teams:", num_teams, \
                         "Seasons:", num_seasons)

            # Table of Contents
            st.markdown("""
            ## Table of Contents
            - [Number of Matches by Competition and Season](#number-of-matches-by-competition-and-season)
            - [Number of Teams per Competition](#number-of-teams-per-competition)
            - [Average Results per Competition](#average-results-per-competition)
            - [Distribution of Match Results](#distribution-of-match-results)
            - [Flat Data](#flat-data)
                - [Competitions Summary Data](#competitions-summary-data)
                - [Competitions Summary with Teams and Season Data](#competitions-summary-with-teams-and-season-data)
                - [Competitions Summary with Teams Data](#competitions-summary-with-teams-data)
                - [Competitions Results Data](#competitions-results-data)                        
            """)


            match_counts = df0.groupby(['competition_name', 'season_name']).size().reset_index(name='number_of_matches')

            # Create a heatmap using Altair
            heatmap = alt.Chart(match_counts).mark_rect().encode(
                x=alt.X('season_name:N', title='Season'),
                y=alt.Y('competition_name:N', title='Competition'),
                color=alt.Color('number_of_matches:Q', title='Number of Matches', scale=alt.Scale(scheme='greens')),
                tooltip=['competition_name:N', 'season_name:N', 'number_of_matches:Q']
            ).properties(
                title='Number of Matches by Competition and Season',
                width=750
            )

            # Display the heatmap in Streamlit
            st.markdown("#### Number of Matches by Competition and Season")
            st.altair_chart(heatmap, use_container_width=True)

            # Chart 1: Number of Teams per Competition
            st.markdown("#### Number of Teams per Competition")
            teams_per_competition = df2.groupby('competition_name')['team_name'].nunique().reset_index()
            teams_per_competition = teams_per_competition.sort_values(by='team_name', ascending=False)
            st.bar_chart(teams_per_competition.set_index('competition_name')['team_name'])

            # Chart 2: Average Results per Competition
            df3['score_difference'] = df3['result'].apply(result_to_score_difference)

            # Calculate average score difference per competition
            average_score_difference_per_competition = df3.groupby('competition_name')['score_difference'].mean().reset_index()
            average_score_difference_per_competition = average_score_difference_per_competition.sort_values(by='score_difference', ascending=False)

            # Create a bar chart using Altair with red bars
            chart = alt.Chart(average_score_difference_per_competition).mark_bar(color='red').encode(
                x=alt.X('competition_name:N', title='Competition'),
                y=alt.Y('score_difference:Q', title='Average Score Difference'),
                tooltip=['competition_name:N', 'score_difference:Q']
            ).properties(
                title='Average Score Difference per Competition',
                width=600
            )
            # Display the chart in Streamlit
            st.markdown("#### Average Results per Competition")
            st.altair_chart(chart, use_container_width=True)

            # Chart 3: Distribution of Match Results
            st.markdown("#### Distribution of Match Results")
            fig3, ax3 = plt.subplots()
            sns.histplot(df3['score_difference'].dropna(), kde=True, ax=ax3, color='blue')  # You can adjust the color as needed
            ax3.set_title('Distribution of Match Results')
            ax3.set_xlabel('Score Difference')
            ax3.set_ylabel('Frequency')
            st.pyplot(fig3)

            st.markdown("#### Flat Data")
            st.write("##### Competitions Summary Data")
            st.dataframe(df)
            st.write("##### Competitions Summary with Teams and Season Data")
            st.dataframe(df0)
            st.write("##### Competitions Summary with Teams Data")
            st.dataframe(df2)
            st.write("##### Competitions Results Data")
            st.dataframe(df3)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    elif menu == "matches":

        sum_matches = 0
        avg_matches = 0
        competitions = 0
        num_teams = 0
        num_seasons = 0

        try:            

            # Table of Contents
            st.markdown("""
                ## Table of Contents
                - [Distribution of Goals per Competition](#distribution-of-goals-per-competition)
                - [Distribution of Goals per Competition per Season](#distribution-of-goals-per-competition-per-season)
                - [Goals Scored by Seasons and Country](#goals-scored-by-seasons-and-country)
                - [Flat Data](#flat-data)                       
            """)

            df = get_all_matches_data(source, True)
            df.index = df.index + 1

            st.markdown("#### Distribution of Goals per Competition")

            goals_scored = df.groupby('competition_name')['goals_scored'].sum().reset_index()
            goals_scored = goals_scored.sort_values(by='goals_scored', ascending=False)

            # Create a bar chart using Altair
            bar_chart = alt.Chart(goals_scored).mark_bar(color='blue').encode(
                x=alt.X('competition_name:N', title='Competition', sort=alt.EncodingSortField(field='goals_scored', order='descending')),
                y=alt.Y('goals_scored:Q', title='Total Goals Scored'),
                tooltip=['competition_name:N', 'goals_scored:Q']
            ).properties(
                title='Total Goals Scored by Competition'
            )

            st.altair_chart(bar_chart, use_container_width=True)

            goals_per_competition_season = df.groupby(['competition_name', 'season_name'])['goals_scored'].sum().reset_index()

            # Create a heatmap using Altair
            heatmap = alt.Chart(goals_per_competition_season).mark_rect().encode(
                x=alt.X('season_name:N', title='Season'),
                y=alt.Y('competition_name:N', title='Competition'),
                color=alt.Color('goals_scored:Q', title='Total Goals Scored', scale=alt.Scale(scheme='greens')),
                tooltip=['competition_name:N', 'season_name:N', 'goals_scored:Q']
            ).properties(
                title='Distribution of Goals per Competition and Season'
            )

            # Display the heatmap in Streamlit
            st.markdown("#### Distribution of Goals per Competition per Season")
            st.altair_chart(heatmap, use_container_width=True)

            # Prepare data for the line chart
            goals_per_season_country = df.groupby(['season_name', 'competition_country'])['goals_scored'].sum().reset_index()

            # Create a line chart using Altair
            line_chart = alt.Chart(goals_per_season_country).mark_line(point=True).encode(
                x=alt.X('season_name:N', title='Season'),
                y=alt.Y('goals_scored:Q', title='Total Goals Scored'),
                color=alt.Color('competition_country:N', title='Country', scale=alt.Scale(scheme='category10')),
                tooltip=['season_name:N', 'goals_scored:Q', 'competition_country:N']
            ).properties(
                title='Goals Scored by Seasons and Country'
            )

            # Display the line chart in Streamlit
            st.markdown("#### Goals Scored by Team Across Seasons and Country")
            st.altair_chart(line_chart, use_container_width=True)

            st.markdown("#### Flat Data")
            st.dataframe(df)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    elif menu == "teams":
         
        try:

            # Table of Contents
            st.markdown("""
                    ## Table of Contents
                    - [Goals Scored by Team Across Seasons](#goals-scored-by-team-across-seasons)
                    - [Goals Scored per Season per Team](#goals-scored-per-season-per-team)
                    - [Total Goals Scored by Team](#total-goals-scored-by-team)
                    - [Total Goals Conceded by Team](#total-goals-conceded-by-team)
                    - [Goals Scored Ratio (Goals Scored to Goals Conceded Ratio)](#goals-scored-ratio-goals-scored-to-goals-conceded-ratio)
                    - [Goals Conceded Ratio (Goals Conceded to Goals Scored Ratio)](#goals-conceded-ratio-goals-conceded-to-goals-scored-ratio)
                    - [Flat Data](#flat-data)                       
            """)

            df = get_all_matches_data(source, True)
            df.index = df.index + 1

            goals_per_team_season = df.groupby(['team_name', 'season_name'])['goals_scored'].sum().reset_index()

            
            st.write("#### Goals Scored by Team Across Seasons")
            # Create a line chart
            line_chart = alt.Chart(goals_per_team_season).mark_line(point=True).encode(
                x=alt.X('season_name:N', title='Season'),
                y=alt.Y('goals_scored:Q', title='Total Goals Scored'),
                color=alt.Color('team_name:N', title='Team', scale=alt.Scale(scheme='category10')),
                tooltip=['team_name:N', 'season_name:N', 'goals_scored:Q']
            ).properties(
                title='Goals Scored by Team Across Seasons'
            )

            st.altair_chart(line_chart, use_container_width=True)

            # Goals Scored per Season per Team
            st.write("#### Goals Scored per Season per Team")
            goals_per_season_team = df.groupby(['team_name', 'season_name'])['goals_scored'].sum().reset_index()

            # Create a scatter plot
            goals_season_scatter = alt.Chart(goals_per_season_team).mark_circle(size=60).encode(
                x=alt.X('season_name:N', title='Season'),
                y=alt.Y('goals_scored:Q', title='Goals Scored'),
                color=alt.Color('team_name:N', title='Team', scale=alt.Scale(scheme='category10')),
                tooltip=['team_name:N', 'season_name:N', 'goals_scored:Q']
            ).properties(
                title='Goals Scored per Season per Team'
            )
            st.altair_chart(goals_season_scatter, use_container_width=True)

            # Filter out Barcelona and Paris Saint-Germain
            st.write("Filter out Barcelona and Paris Saint-Germain due to too much data!")
            df = df[df['team_name'] != 'Barcelona']
            df = df[df['team_name'] != 'Paris Saint-Germain']

            # Calculate goals scored and conceded
            goals_comparison = df.groupby('team_name').agg({
                'goals_scored': 'sum',
                'goals_conceded': 'sum'
            }).reset_index()

            # Calculate ratios
            goals_comparison['goal_scored_ratio'] = (goals_comparison['goals_scored'] / (goals_comparison['goals_conceded'] + 1)).round(2)  # Goals scored ratio
            goals_comparison['goal_conceded_ratio'] = (goals_comparison['goals_conceded'] / (goals_comparison['goals_scored'] + 1)).round(2)  # Goals conceded ratio

            # 1. Total Goals Scored
            st.write("#### Total Goals Scored by Team")
            goals_scored_chart = alt.Chart(goals_comparison).mark_bar(color='skyblue').encode(
                x=alt.X('team_name:N', title='Team', sort=alt.EncodingSortField(field='goals_scored', order='descending')),
                y=alt.Y('goals_scored:Q', title='Total Goals Scored'),
                tooltip=['team_name:N', 'goals_scored:Q']
            ).properties(
                title='Total Goals Scored by Team',
                width=800,
                height=400
            )
            st.altair_chart(goals_scored_chart, use_container_width=True)

            # 2. Total Goals Conceded
            st.write("#### Total Goals Conceded by Team")
            goals_conceded_chart = alt.Chart(goals_comparison).mark_bar(color='salmon').encode(
                x=alt.X('team_name:N', title='Team', sort=alt.EncodingSortField(field='goals_conceded', order='descending')),
                y=alt.Y('goals_conceded:Q', title='Total Goals Conceded'),
                tooltip=['team_name:N', 'goals_conceded:Q']
            ).properties(
                title='Total Goals Conceded by Team',
                width=800,
                height=400
            )
            st.altair_chart(goals_conceded_chart, use_container_width=True)

            # 3. Goals Scored Ratio
            st.write("#### Goals Scored Ratio (Goals Scored to Goals Conceded Ratio)")
            scored_ratio_chart = alt.Chart(goals_comparison).mark_circle(size=60).encode(
                x=alt.X('goal_scored_ratio:Q', title='Goals Scored to Goals Conceded Ratio'),
                y=alt.Y('goals_scored:Q', title='Total Goals Scored'),
                color=alt.Color('team_name:N', title='Team', scale=alt.Scale(scheme='category10')),
                tooltip=['team_name:N', 'goal_scored_ratio:Q', 'goals_scored:Q', 'goals_conceded:Q']
            ).properties(
                title='Goals Scored Ratio per Team'
            )
            st.altair_chart(scored_ratio_chart, use_container_width=True)

            # 4. Goals Conceded Ratio
            st.write("#### Goals Conceded Ratio (Goals Conceded to Goals Scored Ratio)")
            conceded_ratio_chart = alt.Chart(goals_comparison).mark_circle(size=60).encode(
                x=alt.X('goal_conceded_ratio:Q', title='Goals Conceded to Goals Scored Ratio'),
                y=alt.Y('goals_conceded:Q', title='Total Goals Conceded'),
                color=alt.Color('team_name:N', title='Team', scale=alt.Scale(scheme='category10')),
                tooltip=['team_name:N', 'goal_conceded_ratio:Q', 'goals_scored:Q', 'goals_conceded:Q']
            ).properties(
                title='Goals Conceded Ratio per Team'
            )
            st.altair_chart(conceded_ratio_chart, use_container_width=True)

            st.markdown("#### Flat Data")

            df2 = get_teams_summary_data(source, True)
            df2.index = df2.index + 1
            st.dataframe(df)
            st.dataframe(df2)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    elif menu == "players":

        try:

            # Table of Contents
            st.markdown("""
                    ## Table of Contents
                    - [Count of Distinct Players by Competition](#count-of-distinct-players-by-competition)
                    - [Count of Distinct Players by Competition and Season](#count-of-distinct-players-by-competition-and-season)
                    - [Flat Data](#flat-data)
            """)

            df = get_players_summary_data(source, True)

            st.markdown("#### Count of Distinct Players by Competition")

            # Prepare data: Count of Distinct Players by Competition
            players_count_by_competition = df.groupby('competition_name')['player_name'].nunique().reset_index()
            players_count_by_competition.columns = ['competition_name', 'distinct_players_count']

            # Create a bar chart
            bar_chart_competition = alt.Chart(players_count_by_competition).mark_bar(color='skyblue').encode(
                x=alt.X('competition_name:N', title='Competition', sort=alt.EncodingSortField(field='distinct_players_count', order='descending')),
                y=alt.Y('distinct_players_count:Q', title='Number of Distinct Players'),
                tooltip=['competition_name:N', 'distinct_players_count:Q']
            ).properties(
                title='Number of Distinct Players by Competition',
                width=800,
                height=400
            )

            st.altair_chart(bar_chart_competition, use_container_width=True)

            st.markdown("#### Count of Distinct Players by Competition and Season")

            # Prepare data: Count of Distinct Players by Competition and Season
            players_count_by_competition_season = df.groupby(['competition_name', 'season_name'])['player_name'].nunique().reset_index()
            players_count_by_competition_season.columns = ['competition_name', 'season_name', 'distinct_players_count']

            # Create a scatter plot
            scatter_plot = alt.Chart(players_count_by_competition_season).mark_circle(size=60).encode(
                x=alt.X('season_name:N', title='Season'),
                y=alt.Y('distinct_players_count:Q', title='Number of Distinct Players'),
                color=alt.Color('competition_name:N', title='Competition', scale=alt.Scale(scheme='category10')),
                tooltip=['competition_name:N', 'season_name:N', 'distinct_players_count:Q']
            ).properties(
                title='Number of Distinct Players by Competition and Season',
                width=800,
                height=400
            )

            st.altair_chart(scatter_plot, use_container_width=True)

            st.markdown("#### Flat Data")

            df.index = df.index + 1
            st.dataframe(df, width=750)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    elif menu == "events":

        try:

            # Table of Contents
            st.markdown("""
            ## Table of Contents
            - [Most Frequent Play Patterns](#most-frequent-play-patterns)
            - [Heatmap of Play Patterns by Possession Team](#heatmap-of-play-patterns-by-possession-team)
            - [Play Patterns by Competition (Percentage)](#play-patterns-by-competition-percentage)
            - [Play Patterns by Season (Percentage)](#play-patterns-by-season-percentage)
            - [Flat Data](#flat-data)
            """)

            df = get_events_summary_data(source, True)

            st.markdown("Query limited to 250.000 rows.")

            # Prepare data: Most Frequent Patterns
            most_frequent_patterns = df.groupby('play_pattern')['count_events'].sum().reset_index()
            most_frequent_patterns = most_frequent_patterns.sort_values(by='count_events', ascending=False)
            # Create a histogram
            histogram_most_frequent_patterns = alt.Chart(most_frequent_patterns).mark_bar(color='skyblue').encode(
                x=alt.X('play_pattern:N', title='Play Pattern', sort=alt.EncodingSortField(field='count_events', order='descending')),
                y=alt.Y('count_events:Q', title='Count of Events'),
                tooltip=['play_pattern:N', 'count_events:Q']
            ).properties(
                title='Most Frequent Play Patterns'
            )

            st.markdown("#### Most Frequent Play Patterns")
            st.altair_chart(histogram_most_frequent_patterns, use_container_width=True)


            most_frequent_patterns = df.groupby(['play_pattern', 'possession_team'])['count_events'].sum().reset_index()
            most_frequent_patterns = most_frequent_patterns.sort_values(by='count_events', ascending=False)

            df = df[df['possession_team'] != 'Barcelona']
            df = df[df['possession_team'] != 'Paris Saint-Germain']

            # Create a heatmap
            heatmap = alt.Chart(most_frequent_patterns).mark_rect().encode(
                x=alt.X('play_pattern:N', title='Play Pattern', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('possession_team:N', title='Possession Team'),
                color=alt.Color('count_events:Q', title='Count of Events', scale=alt.Scale(scheme='greens')),
                tooltip=['play_pattern:N', 'possession_team:N', 'count_events:Q']
            ).properties(
                title='Heatmap of Play Patterns by Possession Team',
                width=800,
                height=400
            )

            st.markdown("#### Heatmap of Play Patterns by Possession Team")
            st.altair_chart(heatmap, use_container_width=True)



            # Prepare data: Pattern by Competition
            df = get_events_summary_data(source, True)
            pattern_by_competition = df.groupby(['competition_name', 'play_pattern'])['count_events'].sum().reset_index()
            total_events_by_competition = pattern_by_competition.groupby('competition_name')['count_events'].sum().reset_index()
            total_events_by_competition.columns = ['competition_name', 'total_events']

            # Merge total events data
            pattern_by_competition = pattern_by_competition.merge(total_events_by_competition, on='competition_name')
            pattern_by_competition['percentage'] = (pattern_by_competition['count_events'] / pattern_by_competition['total_events'] * 100).round(2)

            # Create a scatter plot
            scatter_pattern_by_competition = alt.Chart(pattern_by_competition).mark_circle(size=60).encode(
                x=alt.X('play_pattern:N', title='Play Pattern', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('percentage:Q', title='Percentage of Total Events'),
                color=alt.Color('competition_name:N', title='Competition', scale=alt.Scale(scheme='category10')),
                tooltip=['competition_name:N', 'play_pattern:N', 'percentage:Q']
            ).properties(
                title='Play Patterns by Competition (Percentage)',
                width=800,
                height=400
            )

            st.markdown("#### Play Patterns by Competition (Percentage)")
            st.altair_chart(scatter_pattern_by_competition, use_container_width=True)

            # Prepare data: Pattern by Season
            pattern_by_season = df.groupby(['season_name', 'play_pattern'])['count_events'].sum().reset_index()
            total_events_by_season = pattern_by_season.groupby('season_name')['count_events'].sum().reset_index()
            total_events_by_season.columns = ['season_name', 'total_events']

            # Merge total events data
            pattern_by_season = pattern_by_season.merge(total_events_by_season, on='season_name')
            pattern_by_season['percentage'] = (pattern_by_season['count_events'] / pattern_by_season['total_events'] * 100).round(2)

            # Create a scatter plot
            scatter_pattern_by_season = alt.Chart(pattern_by_season).mark_circle(size=60).encode(
                x=alt.X('play_pattern:N', title='Play Pattern', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('percentage:Q', title='Percentage of Total Events'),
                color=alt.Color('season_name:N', title='Season', scale=alt.Scale(scheme='category10')),
                tooltip=['season_name:N', 'play_pattern:N', 'percentage:Q']
            ).properties(
                title='Play Patterns by Season (Percentage)',
                width=800,
                height=400
            )

            st.markdown("#### Play Patterns by Season (Percentage)")
            st.altair_chart(scatter_pattern_by_season, use_container_width=True)

            st.markdown("#### Flat Data")

            df = get_events_summary_data(source, True)

            df.index = df.index + 1
            st.dataframe(df)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    elif menu =="chatbot logs":

        st.markdown("### Chat Logs")
        
        # List of files in the 'statistics_files' directory
        directory = "./data/scripts_summary/Answers" 
        try:
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        except FileNotFoundError:
            st.error("Directory not found.")
            files = []
    
        if files:
            selected_file = st.selectbox(
                "Select a file", 
                options=[f for f in files],  # Options based on file names with extension
                index=0  # Optional: Default index
            )

            st.write("number of files: ", len(files))

            if selected_file:
                file_path = os.path.join(directory, selected_file)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='ISO-8859-1') as file:
                            content = file.read()
                    except UnicodeDecodeError:
                        # Try with cp1252 if ISO-8859-1 fails
                        try:
                            with open(file_path, 'r', encoding='cp1252') as file:
                                content = file.read()
                        except Exception as e:
                            st.error(f"Error reading file {selected_file}: {e}")
                            content = None
                    
                    if content:

                        st.write("#### File name: ", selected_file)
                        st.write(content)

                else:
                    st.error(f"File {selected_file} not found.")
        else:
            st.write("No files available in the directory.")


    elif menu == "chatbot":

        call_gpt(source)

    elif menu == "readme":

        filename = "./README-project.md"

        # create the page TOC
        content = load_file(filename)
        toc = extract_headers(content)
        toc_html = generate_toc(toc, 2)
        st.markdown(f'<div style="margin-bottom: 20px;">{toc_html}</div>', unsafe_allow_html=True)

        # load md and replace the hrefs with buttons for streamlit
        load_and_process_hrefs(filename, False)


except Exception as e:
    st.error(f"An error occurred: {str(e)}")
