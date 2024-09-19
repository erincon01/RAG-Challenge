import os
import json
import pandas as pd
from datetime import datetime
from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_data import load_matches_data_into_database_from_folder, load_lineups_data_into_database, load_events_data_into_database
from module_data import download_match_yaml, copy_data_between_sql_sources, get_connection, get_game_result_data
from module_azure_openai import get_tokens_statistics_from_table_column, get_random_dataframe_from_match_id, get_chat_completion_from_azure_open_ai 
from module_azure_openai import create_match_summary, search_details_using_embeddings, process_prompt_from_questions_batch

def sandbox_process_batch(source):

    system_message = f"""Answer the users QUESTION using the EVENTS and GAME_RESULT listed above.
        Keep your answer ground in the facts of the EVENTS or GAME_RESULT.
        If the EVENTS or GAME_RESULT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question. """   

     ###### France - Argentina match_id: 3869685
     ###### England - Spain match_id: 3943043  

    match_id = 3943043
    embeddings_model = "text-embedding-3-small"
    input_tokens = 25000
    output_tokens = 5000
    local_folder = os.getenv('LOCAL_FOLDER')
    
    questions = None
    try:
        # Try to open and load the JSON file
        with open(os.path.abspath("questions.json"), "r") as file:
            questions = json.load(file)
    except Exception as e2:
        questions = None

    if questions is not None: 
        process_prompt_from_questions_batch (source, questions, match_id, embeddings_model, system_message, input_tokens, output_tokens, local_folder, True)


def sandbox_explore_auto_option_for_search():

    # seek for vector search algorithm. 'auto' mode investigation

    system_message = f"""SELECT the appropriate vector search algorithm to answer the QUESTION using the EVENTS_DATASET and GAME_RESULT listed above. 
    Return one of these options: Cosine, Euclidean, or Negative_inner_product.
    Be strong in your analysis before making your decision.
    Use this format in the response: '<Algorithm>: Explanation'. Only Cosine, Euclidean, Negative_inner_product, or None are valid answers."""

    ### If your confidence level is below 70%, return None. 
    # get sample data match_id = 3943043 
    match_id = 3943043 
    source = "azure-sql"

    df_result = get_game_result_data(source, match_id, as_data_frame=True)
    df_events = get_random_dataframe_from_match_id(source, "events_details__15secs_agg", "summary", match_id, 20)

    questions_data = None

    try:
        # Try to open and load the JSON file
        with open(os.path.abspath("questions.json"), "r") as file:
            questions_data = json.load(file)
    except Exception as e2:
        questions_data = None

    if questions_data is not None:
        questions_df = pd.DataFrame(questions_data)
        questions_df["question_auto"] = None
        questions_df["question_auto_explanation"] = None

        rows = questions_df.shape[0]

        # for each question in the data frame
        for index, row in questions_df.iterrows():
            question_number = row["question_number"]
            question = row["question"]
            search_type = row["search_type"]

            header =""

            header += f"\n\nGAME_RESULT\n" + df_result.to_string(index=False, header=False)
            header += "-------------------------------------------------"
            header += f"\n\nEVENTS_DATASET\n" + df_events.to_string(index=False, header=False)
            header += "-------------------------------------------------"
            header+= f"\n\n" +  system_message

            answer = get_chat_completion_from_azure_open_ai(header, question, 0.1, 5000)

            # get the answer
            try:
                search_type_auto = answer.split(":")[0]
                search_type_auto = search_type_auto.replace("*", "")

                # check if search_type_auto is valid
                if search_type_auto.lower() not in ["cosine", "euclidean", "negative_inner_product", "none"]:
                    search_type_auto = "None"
                    answer = "None: No answer found."

            except IndexError:
                search_type_auto = "None"
                answer = "None: No answer found."

            # extract from the answer the first part before :
            questions_df.loc[questions_df["question_number"] == question_number, "question_auto"] = search_type_auto
            questions_df.loc[questions_df["question_number"] == question_number, "question_auto_explanation"] = answer

            # print result
            print(f"QUESTION_NUMBER         : {question_number} - {index + 1}/{rows}")
            print(f"QUESTION                : {question}")
            print(f"ANSWER-QUERY            : {search_type}")
            print(f"ANSWER-AUTO             : {search_type_auto}")
            print(f"ANSWER-AUTO-EXPLANATION : {answer}")
            print("-------------------------------------------------")

        # export the data frame to json
        dir = os.path.abspath("questions_auto.json")
        questions_df.to_json(dir, orient="records", lines=True)
    else:
        print("Failed to load questions data.")


def export_to_Json_details_tables_from_azure_sql():

    # export data to json

    conn_src = get_connection("azure-sql")

    # sql server
    sql_query = "match_id, period, minute, count, json_, summary, cast( embedding_3_small as nvarchar(max)) embedding_3_small , cast( embedding_ada_002 as nvarchar(max)) embedding_ada_002, id"

    df = pd.read_sql("SELECT " + sql_query + " FROM events_details__15secs_agg WHERE not summary is null", conn_src)
    dir = os.path.join(".", "events_details__15secs_agg.json")
    df.to_json(dir, orient="records", lines=True)


    df = pd.read_sql("SELECT " + sql_query + " FROM events_details__15secs_agg_v1 WHERE not summary is null", conn_src)
    dir = os.path.join(".", "events_details__15secs_agg_v1.json")
    df.to_json(dir, orient="records", lines=True)


def export_to_Json_details_tables_from_azure_postgres():

        # export data to json

    conn_src = get_connection("azure-postgres")

    # postgres
    sql_query = "match_id, period, minute, count, json_, summary, summary_script, cast( summary_embedding_t3_large as text) summary_embedding_t3_large , cast( summary_embedding_t3_small as text) summary_embedding_t3_small , cast( summary_embedding_ada_002 as text) summary_embedding_ada_002 , id"

    cursor = conn_src.cursor()

    cursor.execute("SELECT " + sql_query + " FROM events_details__minutewise WHERE not summary is null")
    rows = cursor.fetchall()
    dir = os.path.join(".", "events_details__minutewise.json")
    with open(dir, 'w') as f:
        for row in rows:
            f.write(json.dumps(row) + '\n')


    cursor.execute("SELECT " + sql_query + " FROM events_details__quarter_minute WHERE not summary is null")
    rows = cursor.fetchall()
    dir = os.path.join(".", "events_details__quarter_minute.json")
    with open(dir, 'w') as f:
        for row in rows:
            f.write(json.dumps(row) + '\n')


def export_to_Yaml_details_tables_from_azure_sql():

    ###### Euro Final 2024     : England - Spain match_id: 3943043
    ###### FIFA World CUP 2022 : France - Argentina match_id: 3869685
    # download summary from match_id 3943043

    download_match_yaml("azure-sql", "events_details__15secs_agg", 3943043, "summary", local_folder + "/openai/matches_summary", 15)
    download_match_yaml("azure-sql", "events_details__15secs_agg_v1", 3943043, "summary", local_folder + "/openai/matches_summary", 15)
    download_match_yaml("azure-sql", "events_details__minute_agg", 3943043, "summary", local_folder + "/openai/matches_summary", 15)


def export_to_Yaml_details_tables_from_azure_postgres():

    ###### Euro Final 2024     : England - Spain match_id: 3943043
    ###### FIFA World CUP 2022 : France - Argentina match_id: 3869685
    # download summary from match_id 3943043

    download_match_yaml("azure-postgres", "events_details__minute_agg", 3943043, "summary", local_folder + "/openai/matches_summary", 15)
    download_match_yaml("azure-postgres", "events_details__minute_agg", 3869685, "summary", local_folder + "/openai/matches_summary", 15)


if __name__ == "__main__":

    # 1) download data from the github repository
    # download_data_from_github_repo()

    # 2) load the data into the database
    # load_matches_data_into_database_from_folder()

    # 3) load lineups data into the database
    # load_lineups_data_into_database()

    # 4) load events data into the database
    # load_events_data_into_database()

    # 5) copy data between sql sources
    # copy_data_between_sql_sources("azure-sql", "azure-postgres", "events_details__15secs_agg", "events_details__15secs_agg", "match_id = 3943043")

    # 6) get game result data
    # get_game_result_data("azure-sql", 3943043, as_data_frame=True)

    # 7) search details using embeddings
    # search_details_using_embeddings("azure-postgres", 3943043, "yes", "Cosine", "text-embedding-3-small", "system_message", "search_term", 10, 0.1, 2000, 5000)

    # 8) create a summary of the match
    # create_match_summary("azure-sql", "events_details__minute_agg", 3943043, "system_message", 0.1, 15000)

    # 9) download from database the scripts in minutes chunks
    # download_match_script("azure-sql", "events_details__minute_agg", 3943043, "summary", "local_folder", 10)
    # download_match_script("azure-sql", "events_details__minute_agg", 3943043, "summary_script", "local_folder", 10)

    # 10) get tokens statistics from a table column
    # get_tokens_statistics_from_table_column('azure-sql', "events_details__quarter_minute", "json_", "match_id = 3943043", -1)

    # 11) prompts calls to the model
    # process_prompt_from_questions_batch()

    # sandbox_process_batch("azure-postgres")
    # sandbox_process_batch("azure-sql")
    
    # sandbox_explore_auto_option_for_search()

    # export_to_Json_details_tables_from_azure_sql()
    # export_to_Json_details_tables_from_azure_postgres()

    # export_to_Yaml_details_tables_from_azure_sql()
    # export_to_Yaml_details_tables_from_azure_postgres()

#     input_tokens = 2000
#     output_tokens = 5000
#     embeddings_model="multilingual-e5-small:v1"
#     search_type="Cosine"
#     temperature = 0.1
#     top_n = 10
#     system_message = f"""Answer the users QUESTION using the DOCUMENT text above.
# Keep your answer ground in the facts of the DOCUMENT.
# If the DOCUMENT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question." """   


#     search_term = "Count the successful passes did each team complete in the first half (minutes 41-47) and the second half (minutes 45-50), and what impact did these passes have on their game performance?"

#     match_id = 3943043
#     include_lineups = "yes"



#     search_details_using_embeddings("azure-postgres", 3943043, "yes", \
#                                     search_type, embeddings_model, \
#                                     system_message, search_term, \
#                                     top_n, temperature, input_tokens, output_tokens)

    # # statsbomb data parameters
    # repo_owner = os.getenv('REPO_OWNER')
    # repo_name = os.getenv('REPO_NAME')
    # local_folder = os.getenv('LOCAL_FOLDER')
    
    # # sql paas database parameters
    # server_azure = os.getenv('DB_SERVER_AZURE')
    # database_azure = os.getenv('DB_NAME_AZURE')
    # username_azure = os.getenv('DB_USER_AZURE')
    # password_azure = os.getenv('DB_PASSWORD_AZURE')

    ###### Euro Final 2024     : England - Spain match_id: 3943043
    ###### FIFA World CUP 2022 : France - Argentina match_id: 3869685

    # 8) create a summary of the match. One call to OpenAI API with all the script.
    # The summary is stored in a file in the folder scripts_summary

    # system_message = """
    #         Make a summary of this match. It's a football match, and I am providing all the game actions.
    #         Include the game result, team's lineup, and most relevant actions such as goals, penalties, and injuries, and cards only if players are sent off. 
    #         Do not invent any information, relate stick to the data. 
    #         When mentioning relevant actions indicate the minute of the match. Relate in prose format the goals. 
    #         Include two sections: data relevant for analysis, and a brief description of the match in prose format.
    #         this is the text:
    #         """

    # match_id = 3943043

    # summary = create_match_summary ("azuresql", "events_details__minute_agg", match_id, system_message, 0.1, 15000)
    # print(summary)
    
    # folder = os.path.join(local_folder, "scripts_summary")
    # filename = f"summary_{match_id}.txt"
    
    # with open(os.path.join(local_folder, folder, filename), "w", encoding="utf-8") as f:
    #     f.write(summary)
    # print(summary)

    # # 9) download from database the scripts in minutes chunks
    # # The summary is stored in a file in the folder scripts_summary

    # local_folder = os.getenv('LOCAL_FOLDER')
    # local_folder = os.path.join(local_folder, "scripts_summary")
    # download_match_script("azuresql", "events_details__minute_agg", 3943043, "summary", local_folder, 10)
    # download_match_script("azuresql", "events_details__minute_agg", 3943043, "summary_script", local_folder, 10)


    # 10) get tokens statistics from a table column
    # usefull to understand the distribution of tokens in a column for embedding purposes

    ###### France - Argentina match_id: 3869685
    ###### England - Spain match_id: 3943043

    # s = get_tokens_statistics_from_table_column('azuresql', "events_details__quarter_minute", "json_", "match_id = 3943043", -1)
    # print (s)

    # s = get_tokens_statistics_from_table_column('azuresql', "events_details__quarter_minute", "summary", "match_id = 3943043", -1)
    # print (s)

    # 11) prompts calls to the model
    
#     input_tokens = 2000
#     output_tokens = 5000
#     selected_model="text-embedding-3-large"
#     selected_search_type="Cosine"
#     temperature = 0.1
#     top_n = 10
#     system_message = f"""Answer the users QUESTION using the DOCUMENT text above.
# Keep your answer ground in the facts of the DOCUMENT.
# If the DOCUMENT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question." """   

#     match_id = 3943043
#     include_lineups = "yes"

#     question = "What were the key moments for each team in minutes 80 to 90 and how affected the result?"
#     dataframe, result = search_details_using_embeddings(source, match_id, selected_search_type, selected_model, True, question, \
#                                     system_message, top_n, temperature, input_tokens, output_tokens)


#     print (result)
#     print (dataframe)
