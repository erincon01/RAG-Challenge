
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
from datetime import datetime
from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_postgres import load_matches_data_into_postgres_from_folder, load_lineups_data_into_postgres, load_events_data_into_postgres
from module_postgres import copy_data_from_postgres_to_azure, download_match_script
from module_azureopenai import get_tokens_statistics_from_table_column, create_events_summary_per_pk_from_json_rows_in_database 
from module_azureopenai import create_and_download_detailed_match_summary, create_match_summary, search_details_using_embeddings, process_prompt_from_web



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

    # 11) prompts calls to the model

        # {"question_number": "Q-001", "top_n": 10, "search_type": "Cosine", "question": "Count the successful passes did each team complete in the first half (minutes 41-47) and the second half (minutes 45-50), and what impact did these passes have on their game performance?"},
        # {"question_number": "Q-001b", "top_n": 10, "include_lineups":"no", "search_type": "Cosine", "question": "Count the successful passes did each team complete in the first half (minutes 41-47) and the second half (minutes 45-50)"},
        # {"question_number": "Q-002", "top_n": 10, "search_type": "Cosine", "question": "Which players recorded the highest number of carries and passes in both halves, and how did their performances influence the overall strategies of the teams?"},
        # {"question_number": "Q-002b", "top_n": 10, "include_lineups":"no", "temperature":"0.5", "search_type": "Cosine", "question": "Which players recorded the highest number of carries and passes in both halves in minutes 15 to 30?"},
        # {"question_number": "Q-002c", "top_n": 10, "include_lineups":"no", "temperature":"0.6", "search_type": "Cosine", "question": "Which players recorded the highest number of carries and passes in both halves in minutes 15 to 30 and impact in the game performance?"}
        # {"question_number": "Q-002d", "top_n": 10, "include_lineups":"no", "temperature":"0.5", "search_type": "Cosine", "question": "Which players recorded the highest number of carries and passes in minutes between 15 to 30?"},
        # {"question_number": "Q-002e", "top_n": 10, "include_lineups":"no", "temperature":"0.6", "search_type": "Cosine", "question": "Count the number of carries and passes per team in minutes between 15 to 30"}
        # {"question_number": "Q-003", "top_n": 10, "search_type": "Cosine", "question": "What were the average pass lengths for each team in each half, and which team showed higher pass accuracy by comparing completed passes to incomplete ones?"},
        # {"question_number": "Q-003b", "top_n": 10, "search_type": "Cosine", "include_json":"yes", "question": "What were the average pass lengths in minutes between 30 and 45?"},
        # {"question_number": "Q-003c", "top_n": 10, "search_type": "InnerP", "include_json":"yes", "question": "What were the average pass lengths in minutes between 30 and 40?"},
        # {"question_number": "Q-004", "top_n": 10, "search_type": "Cosine", "question": "How did the possession percentages of each team change during the first and second halves, and what key moments or events caused these fluctuations?"},
        # {"question_number": "Q-004b", "top_n": 10, "search_type": "Cosine", "temperature":"0.5", "question": "What were the key moments for each team in minutes 80 to 90 and how affected the result?"},
        # {"question_number": "Q-005", "top_n": 10, "search_type": "Cosine", "question": "How many defensive actions, such as tackles, saves, and blocks, did each team execute, and show the top 3 players in these actions for each team?"},
        # {"question_number": "Q-005b", "top_n": 10, "search_type": "Cosine", "question": "What defensive actions, such as tackles, saves, and blocks, did each team execute in second half?"},
        # {"question_number": "Q-006", "top_n": 10, "search_type": "Cosine", "question": "How many shots on goal did each team take, splitted in 30 minutes timeframes?"},
        # {"question_number": "Q-006c", "top_n": 10, "search_type": "InnerP", "question": "What shots on goal did each team take, in minutes between 60 and 90?"},
        # {"question_number": "Q-006d", "top_n": 10, "search_type": "InnerP", "question": "Show details of the goals scored"},
        # {"question_number": "Q-006d", "top_n": 10, "search_type": "InnerP", "temperature":"0.5", "question": "Show details of the goals scored"},
        # {"question_number": "Q-006d", "top_n": 10, "search_type": "Cosine", "temperature":"0.5", "question": "Show details of the goals scored"}
        # {"question_number": "Q-006e", "top_n": 10, "search_type": "InnerP", "model":"text-embedding-3-large", "temperature":"0.5", "question": "Show details of the goals scored"},
        # {"question_number": "Q-006e", "top_n": 10, "search_type": "Cosine", "model":"text-embedding-3-large", "temperature":"0.5", "question": "Show details of the goals scored"}
        # {"question_number": "Q-006e", "top_n": 10, "search_type": "InnerP", "model":"text-embedding-3-large", "temperature":"0.5", "question": "Show details of the goals scored"},
        # {"question_number": "Q-006e", "top_n": 10, "search_type": "Cosine", "model":"text-embedding-3-large", "temperature":"0.5", "question": "Show details of the goals scored"}
        # {"question_number": "Q-007", "top_n": 10, "search_type": "Cosine", "question": "Which areas on the pitch had the highest concentration of passes, carries, and key actions for both teams during the match?"},
        # {"question_number": "Q-007c", "top_n": 10, "search_type": "Cosine", "temperature":"0.5", "include_json":"yes", "question": "Which areas on the pitch had the highest concentration of passes, carries, and key actions for both teams in minutes between 30 and 40?"},
        # {"question_number": "Q-008", "top_n": 10, "search_type": "Cosine", "question": "How many aerial duels and one-on-one challenges did each team engage in, and what were their respective success rates in these confrontations?"},
        # {"question_number": "Q-008c", "top_n": 10, "search_type": "Cosine", "temperature":"0.5", "include_json":"yes", "question": "How many aerial duels and one-on-one challenges did each team engage in in minutes between 15 to 25"}
        # {"question_number": "Q-010", "top_n":  5, "search_type": "InnerP", "question": "List the critical moments or sequences, such as blocked shots, successful tackles, and goal attempts"},
        # {"question_number": "Q-011", "top_n":  5, "search_type": "InnerP", "question": "What was the final scoreline of the match, including goals scored by each team and any additional time or penalty shootout results?"},
        # {"question_number": "Q-012", "top_n":  5, "search_type": "InnerP", "question": "Who scored the goals for each team in which minutes, and what types of goals were they, such as headers or penalties?"},
        # {"question_number": "Q-013", "top_n":  5, "search_type": "InnerP", "question": "How did the home and visiting teams perform based on metrics like possession, pass accuracy, shots on target, and defensive actions?"},
        # {"question_number": "Q-014", "top_n":  5, "search_type": "InnerP", "question": "Were there any yellow or red cards issued during the match, specifying the players involved and the reasons for the bookings?"},
        # {"question_number": "Q-015b", "top_n":  5, "search_type": "Cosine", "temperature":"0.5", "question": "Who was the best player in minutes between 80 and 100?"}
        # {"question_number": "Q-016", "top_n":  5, "search_type": "InnerP", "question": "What strategies or tactical formations did both teams employ, and how did these influence the outcome of the match?"},
        # {"question_number": "Q-017", "top_n":  5, "search_type": "InnerP", "question": "How did the decisions of the referee, such as fouls and penalties, influence the flow and outcome of the game?"},
        # {"question_number": "Q-018", "top_n":  5, "search_type": "InnerP", "question": "Were there any significant injuries during the match, detailing the players affected and the impact on their teams?"},
        # {"question_number": "Q-019", "top_n": 10, "search_type": "Cosine", "question": "Which players were most effective in disrupting the play of the the opponent through tackles, interceptions, and defensive actions?"}

     questions = [
        {"question_number": "Q-011", "top_n":  5, "search_type": "InnerP", "question": "What was the final scoreline of the match, including goals scored by each team and any additional time or penalty shootout results?"},
        {"question_number": "Q-012", "top_n":  5, "search_type": "InnerP", "question": "Who scored the goals for each team in which minutes, and what types of goals were they, such as headers or penalties?"}
    ]
     
    #  system_message = f"""
    #         Answer the users QUESTION using the DOCUMENT text above.
    #         Keep your answer ground in the facts of the DOCUMENT.
    #         If the DOCUMENT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question."
    #     """   

    #  ###### France - Argentina match_id: 3869685
    #  ###### England - Spain match_id: 3943043  

    #  match_id = 3943043

    #  input_tokens = 25000
    #  output_tokens = 5000
    #  local_folder = os.getenv('LOCAL_FOLDER')

    #  process_prompt (questions, match_id, system_message, input_tokens, output_tokens, local_folder)



     input_tokens = 2000
     output_tokens = 5000
     selected_model="text-embedding-3-large"
     selected_search_type="Cosine"
     temperature = 0.1
     top_n = 10
     system_message = f"""Answer the users QUESTION using the DOCUMENT text above.
Keep your answer ground in the facts of the DOCUMENT.
If the DOCUMENT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question." """   

     match_id = 3943043
     include_lineups = "yes"

     question = "What were the key moments for each team in minutes 80 to 90 and how affected the result?"
     dataframe, result = process_prompt_from_web (match_id, selected_model, \
                                 selected_search_type, top_n, include_lineups, temperature, \
                                 system_message, question, input_tokens, output_tokens)
     
     print (result)
     print (dataframe)


