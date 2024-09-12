
"""
        This script performs various operations related to downloading, storing, and summarizing football match data.
        The script follows the following steps:
        1. Download all matches data from a GitHub repository to a local folder.
        2. Store the downloaded matches data into a PostgreSQL database.
        3. Get lineups and events data from the GitHub repository based on the matches stored in the database.
        4. Load the downloaded data into PostgreSQL from the local folder.
        5. Copy data from the local PostgreSQL database to an Azure database.
        6. Convert each row of JSON data into a prose script.
        7. Create a detailed match summary based on the summaries of each event.
        8. Create a summary of the match using OpenAI API.
        9. Download the scripts in minute chunks from the database.
        10. Get token statistics from a table column.
        Please note that this script requires environment variables to be set for various parameters such as repository owner, repository name, local folder path, database server, database name, database username, database password, and Azure database server, database name, username, and password.
        The script is divided into several functions, each performing a specific task. The main function is executed when the script is run as a standalone program.
        For more details on each step and the parameters used, please refer to the comments in the code.
"""

import os
from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_postgres import load_matches_data_into_postgres_from_folder, load_lineups_data_into_postgres, load_events_data_into_postgres
from module_postgres import copy_data_from_postgres_to_azure, download_match_script
from module_azureopenai import get_tokens_statistics_from_table_column, create_events_summary_per_pk_from_json_rows_in_database
from module_azureopenai import create_and_download_detailed_match_summary, create_match_summary, search_details_using_bindings

if __name__ == "__main__":

#     # statsbomb data parameters
#     repo_owner = os.getenv('REPO_OWNER')
#     repo_name = os.getenv('REPO_NAME')
#     local_folder = os.getenv('LOCAL_FOLDER')
    
#     # postgres database parameters
#     server = os.getenv('DB_SERVER')
#     database = os.getenv('DB_NAME')
#     username = os.getenv('DB_USER')
#     password = os.getenv('DB_PASSWORD')

#     # postgres database parameters
#     server_azure = os.getenv('DB_SERVER_AZURE')
#     database_azure = os.getenv('DB_NAME_AZURE')
#     username_azure = os.getenv('DB_USER_AZURE')
#     password_azure = os.getenv('DB_PASSWORD_AZURE')

#     # 1) download all matches data from GitHub repository (statsbomb) to local folder
#     download_data_from_github_repo(repo_owner, repo_name, "matches", local_folder)

#     # 2) store into the database the matches data
#     load_matches_data_into_postgres_from_folder(local_folder)

#     # 3) get lineups and events data, based on the matches stored in the database. 
#     #    this method only downloads the data from the repository into the local folder.
#     #    it does not store the data into the database.
#     get_github_data_from_matches(repo_owner, repo_name, "lineups", local_folder)
#     get_github_data_from_matches(repo_owner, repo_name, "events", local_folder)


#     # 4) load downloadded data into PostgreSQL from local folder
#     load_lineups_data_into_postgres(local_folder)
#     load_events_data_into_postgres(local_folder)

#     # 5) copy data from local to azure

###### France - Argentina match_id: 3869685
###### England - Spain match_id: 3943043

    # # matches table
    # table_name = "matches"
    # table_columns = "match_id, match_date, competition_id, competition_country, competition_name, season_id, season_name, home_team_id, home_team_name, home_team_gender, home_team_country, home_team_manager, home_team_manager_country, away_team_id, away_team_name, away_team_gender, away_team_country, away_team_manager, away_team_manager_country, home_score, away_score, result, match_week, stadium_id, stadium_name, stadium_country, referee_id, referee_name, referee_country, json_"
    # copy_data_from_postgres_to_azure(table_name, table_columns, 3869685)

    # # lineups table
    # table_name = "lineups"
    # table_columns = "match_id, home_team_id, home_team_name, away_team_id, away_team_name, json_"
    # copy_data_from_postgres_to_azure(table_name, table_columns, 3869685)

    # # players table
    # table_name = "players"
    # table_columns = "match_id, team_id, team_name, player_id, player_name, jersey_number, country_id, country_name, position_id, position_name, from_time, to_time, from_period, to_period, start_reason, end_reason"
    # copy_data_from_postgres_to_azure(table_name, table_columns, 3869685)

    # # events table
    # table_name = "events"
    # table_columns = "match_id, json_"
    # copy_data_from_postgres_to_azure(table_name, table_columns, 3869685)

#     # # events_details table
#     # this table is loaded using the script /postgres/tables_setup_load_events_details_from_postgres.sql
#     # reason is because it is more efficient to build the data using json functions in postgres vs trasnferring the data row by row


#     # 6-a) convert each json_ row into a prose script (line by line)

                ###### France - Argentina match_id: 3869685
                ###### England - Spain match_id: 3943043

    # system_message = """
    #         Describe the message in English. It's a football match, and I am providing the detailed actions in Json format ordered minute by minute how action how they happenned.
    #         By using the id, and related_events columns you can cross-relate events. There may be some hierachies. Mention the players in the script.
    #         Do not invent any information. Do relate stick to the data. 
    #         In special events like: goal sucessful, goal missed, shoots to goal, and goalkeeper saves relate like a commentator highlighting the action mentioning time, and score changes if apply.
    #         Relate in prose format. Use the word keeper instead of goalkeeper.
    #         Do not make intro like "In the early moments of the match", "In the openning", etc. Just start with the action.
    #         At the end include one sentence as a brief description of what happened starting with "Summary:"
    #         This is the Json data: 
    #         """

    # create_events_summary_per_pk_from_json_rows_in_database ("azure", "events_details__quarter_minute", "id", "summary", 3869685, -1, system_message, 0.1, 7500)

    # # 6-b) convert each json_ row into a prose script (line by line). in this case it is agnostic of the timing, it is based on the primary key column

    # system_message = """
    #         Describe the message in English using this pattern: # | action type | mm:ss | player name | action | player location | location translation | related player | result. 
    #         be bold in goal sucessful, goal missed, goal blocked, shoots to goal, and goalkeeper saves. do not use special marks.
    #         It's a football match, and I am providing the detailed actions in Json format ordered minute by minute.
    #         By using the Id column you can cross-relate events. There may be some hierachies.
    #         Do not invent any information. Do relate stick to the data, and do not include any personal opinion.
    #         This is the Json data: 
    #         """
    
    # create_events_summary_per_pk_from_json_rows_in_database ("azure", "events_details__minutewise", "id", "summary_script", 3943043, -1, system_message, 0.1, 7500)

#     # 7) create a detailed match summary of the match based on the summaries of each event created in 5)
#     # data is aggegated using the parameter rows_per_prompt
#     # this this create several files split by file_prompt_size
    
#     # For a given match_id, create a summary of the match. Key considerations:
#     # - system_message: the message to be used in the summary
#     # - rows_per_prompt: the number of rows to be used in each prompt
#     # - file_prompt_size: the number of files to be used in each prompt
#     # - temperature: the temperature to be used in the model
#     # - tokens: the maximum number of tokens to be generated

#     system_message = """
#             Make a summary of this batch of play-by-play commentaries.
#             It's a football match, and I am providing the detailed actions in prose ordered minute by minute.
#             Include the most relevant actions such as goals, penalties, and injuries, and cards only if players are sent off. 
#             Do not invent any information, relate stick to the data, and do not include any personal opinion. 
#             Relate in prose format. this is the text:
#             """
    
#     local_folder = os.getenv('LOCAL_FOLDER')
#     local_folder = os.path.join(local_folder, "scripts")
#     match_id = 3943043
#     rows_per_prompt = 20
#     file_prompt_size = 10

#     create_and_download_detailed_match_summary (match_id, rows_per_prompt, file_prompt_size, 0.1, system_message, 15000, local_folder)

#     # 8) create a summary of the match. One call to OpenAI API with all the script.
#     # The summary is stored in a file in the folder scripts_summary

#     system_message = """
#             Make a summary of this match. It's a football match, and I am providing all the game actions.
#             Include the game result, team's lineup, and most relevant actions such as goals, penalties, and injuries, and cards only if players are sent off. 
#             Do not invent any information, relate stick to the data. 
#             When mentioning relevant actions indicate the minute of the match. Relate in prose format the goals. 
#             Include two sections: data relevant for analysis, and a brief description of the match in prose format.
#             this is the text:
#             """

#     match_id = 3943043

#     summary = create_match_summary ("Azure", "events_details__minutewise", match_id, system_message, 0.1, 15000)
#     print(summary)
    
#     folder = os.path.join(local_folder, "scripts_summary")
#     filename = f"summary_{match_id}.txt"
    
#     with open(os.path.join(local_folder, folder, filename), "w", encoding="utf-8") as f:
#         f.write(summary)
#     print(summary)

    # # 9) download from database the scripts in minutes chunks
    # # The summary is stored in a file in the folder scripts_summary

    # local_folder = os.getenv('LOCAL_FOLDER')
    # local_folder = os.path.join(local_folder, "scripts_summary")
    # download_match_script("azure", "events_details__minutewise", 3943043, "summary", local_folder, 10)
    # download_match_script("azure", "events_details__minutewise", 3943043, "summary_script", local_folder, 10)


    # 10) get tokens statistics from a table column
    # usefull to understand the distribution of tokens in a column for embedding purposes

    ###### France - Argentina match_id: 3869685
    ###### England - Spain match_id: 3943043

    # s = get_tokens_statistics_from_table_column('azure', "events_details__quarter_minute", "json_", "match_id = 3943043", -1)
    # print (s)

    # s = get_tokens_statistics_from_table_column('azure', "events_details__quarter_minute", "summary", "match_id = 3943043", -1)
    # print (s)

    # 11) goals scored in a match

    ###### France - Argentina match_id: 3869685
    ###### England - Spain match_id: 3943043

     match_id = 3943043

     search_term = "Goals conceeded"
     system_message = f"""
            Summarize the actions like highlight for these search term: ** {search_term} **.
            Do not invent any information, relate stick to the data. 
            this is the text:
            """     

     summary = search_details_using_bindings ("Azure", "events_details__quarter_minute", match_id, "Spain", search_term, system_message, 0.1, 5000)
     print(summary)

