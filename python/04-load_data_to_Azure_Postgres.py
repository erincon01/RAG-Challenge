
import os
from datetime import datetime
from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_postgres import load_matches_data_into_postgres_from_folder


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
