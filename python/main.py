"""
Main script for loading data from GitHub and storing it in a PostgreSQL database.
This script retrieves data from a GitHub repository and saves it locally. Then, it loads the data into a PostgreSQL database.

Environment variables:
- REPO_OWNER: The owner of the GitHub repository.
- REPO_NAME: The name of the GitHub repository.
- DATASETS: Comma-separated list of datasets to download from the repository.
- local_folder: The destination directory to save the downloaded datasets.
- DIR_FUENTE: The source directory containing the downloaded datasets.
- DB_SERVER: The server address of the PostgreSQL database.
- DB_NAME: The name of the PostgreSQL database.
- DB_USER: The username for accessing the PostgreSQL database.
- DB_PASSWORD: The password for accessing the PostgreSQL database.

Functions:
- put_data_into_postgres: Loads data from the source directory into the PostgreSQL database.
- update_embeddings: Updates embeddings in the specified table using the specified model.

Usage:
1. Set the required environment variables.
2. Run the script.
Note: The script assumes that the necessary modules 'module_github' and 'module_postgresql' are available.
"""

import os
from module_github import get_github_data, get_github_data_from_matches
from module_postgresql import load_matches_data_into_db, load_lineups_data, load_events_data, copy_data_from_local_to_azure, convert_json_to_summary, match_summary, export_match_summary_minutes

if __name__ == "__main__":

    # statsbomb data parameters
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')
    local_folder = os.getenv('LOCAL_FOLDER')
    
    # postgres database parameters
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    # postgres database parameters
    server_azure = os.getenv('DB_SERVER_AZURE')
    database_azure = os.getenv('DB_NAME_AZURE')
    username_azure = os.getenv('DB_USER_AZURE')
    password_azure = os.getenv('DB_PASSWORD_AZURE')

    openai_model = os.getenv('OPENAI_MODEL')
    openai_key = os.getenv('OPENAI_KEY')
    openai_endpoint = os.getenv('OPENAI_ENDPOINT')
    openai_temperature = float(os.getenv('OPENAI_TEMPERATURE', 0.1))    
    content = os.getenv('MESSAGE_HEADER')





    # 1) download all matches data from GitHub repository (statsbomb) to local folder
    # get_github_data(repo_owner, repo_name, "matches", local_folder)

    # 2) store into the database the matches data
    # load_matches_data_into_db(local_folder, server, database, username, password)

    # 3) get lineups and events data, based on the matches stored in the database. 
    #    this method only downloads the data from the repository into the local folder.
    #    it does not store the data into the database.
    # get_github_data_from_matches(repo_owner, repo_name, "lineups", local_folder, server, database, username, password)
    # get_github_data_from_matches(repo_owner, repo_name, "events", local_folder, server, database, username, password)


    # 4) load downloadded data into PostgreSQL from local folder
    # load_lineups_data(server, database, username, password, local_folder)
    # load_events_data(server, database, username, password, local_folder)

    # 5) copy data from local to azure

    ## matches table
    # table_name = "matches"
    # table_columns = "match_id, match_date, competition_id, competition_country, competition_name, season_id, season_name, home_team_id, home_team_name, home_team_gender, home_team_country, home_team_manager, home_team_manager_country, away_team_id, away_team_name, away_team_gender, away_team_country, away_team_manager, away_team_manager_country, home_score, away_score, result, match_week, stadium_id, stadium_name, stadium_country, referee_id, referee_name, referee_country, json_"
    # copy_data_from_local_to_azure(server, database, username, password, server_azure, 
    #                               database_azure, username_azure, password_azure,
    #                               table_name, table_columns)

    ## lineups table
    # table_name = "lineups"
    # table_columns = "match_id, home_team_id, home_team_name, away_team_id, away_team_name, json_"
    # copy_data_from_local_to_azure(server, database, username, password, server_azure, 
    #                               database_azure, username_azure, password_azure,
    #                               table_name, table_columns)

    ## players table
    # table_name = "players"
    # table_columns = "match_id, team_id, team_name, player_id, player_name, jersey_number, country_id, country_name, position_id, position_name, from_time, to_time, from_period, to_period, start_reason, end_reason"
    # copy_data_from_local_to_azure(server, database, username, password, server_azure, 
    #                               database_azure, username_azure, password_azure,
    #                               table_name, table_columns)

    # # events table
    # table_name = "events"
    # table_columns = "match_id, json_"
    # copy_data_from_local_to_azure(server, database, username, password, server_azure, 
    #                               database_azure, username_azure, password_azure,
    #                               table_name, table_columns)

    # # events_details table
    # this table is loaded using the script /postgres/tables_setup_load_events_details_from_postgres.sql
    # reason is because it is more efficient to build the data using json functions in postgres vs trasnferring the data row by row


    # For azure_open_ai or azure_local_ai
#     model = "azure_local_ai"  # azure_open_ai,
#     ### azure_local_ai (see azure_open_ai documentation, only supported in specific regions and Memory Optimized, E4ds_v5, 4 vCores, 32 GiB RAM, 128 GiB storage)

#     convert_json_to_summary(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", 3943043,
#                             openai_endpoint, openai_key, "gpt-4o-mini", 0.1, 8000, content)

    
    content = """
            Make a summary of the match. 
            Include the game result, and most relevant actions such as goals, penalties, and injuries, and cards only if players are sent off. 
            Do not invent any information, relate stick to the data. 
            Relate in prose format the goals.
            Include two sections: data relevant for analysis, and a brief description of the match in prose format: 
            """

    match_id = 3943043
    summary = match_summary(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", match_id,
                          openai_endpoint, openai_key, "gpt-4o-mini", 0.1, 15000, content)
    
    folder = os.path.join(local_folder, "scripts_summary")
    filename = f"summary_{match_id}.txt"

    with open(os.path.join(local_folder, folder, filename), "w", encoding="utf-8") as f:
        f.write(summary)

    print(summary)
     
    export_match_summary_minutes(server_azure, database_azure, username_azure, password_azure, "final_match_Spain_England_events_details__minutewise", 3943043, folder, 10)



