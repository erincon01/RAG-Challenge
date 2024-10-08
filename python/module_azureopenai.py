import os
import tiktoken
import statistics
import psycopg2
from psycopg2 import sql
import pandas as pd
from openai import AzureOpenAI
import datetime
from datetime import datetime
import traceback
from module_postgres import get_game_result_data, get_game_players_data, get_json_events_details_from_match_id

def get_connection(source):
    
    conn = None

    if source.lower() == "azure":
        # Connect to the Azure database
        conn = psycopg2.connect(
            host=os.getenv('DB_SERVER_AZURE'),
            database=os.getenv('DB_NAME_AZURE'),
            user=os.getenv('DB_USER_AZURE'),
            password=os.getenv('DB_PASSWORD_AZURE')
        )
    else:
        # Connect to the Azure database
        conn = psycopg2.connect(
            host=os.getenv('DB_SERVER'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

    return conn

def get_chat_completion_from_azure_open_ai(system_message, user_prompt, temperature, tokens):
    """
    Retrieves a chat completion from Azure OpenAI API.
    Args:
        system_message (str): The system message.
        user_prompt (str): The user prompt.
        temperature (float): The temperature value for generating chat completions.
        tokens (int): The maximum number of tokens for generating chat completions.
    Returns:
        str: The generated chat completion.
    """
    client = AzureOpenAI(
        azure_endpoint=os.getenv('OPENAI_ENDPOINT'),
        api_key=os.getenv('OPENAI_KEY'),
        api_version="2023-05-15"
    )

    response = client.chat.completions.create(
        model=os.getenv('OPENAI_MODEL'),
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=tokens,
    )

    output = response.choices[0].message.content

    output = output.replace('\n\n', '\n').replace('\n\n', '\n')

    return output

def count_tokens(prompt):
    """
    Counts the number of tokens in the given prompt.
    Parameters:
    prompt (str): The prompt to count tokens from.
    Returns:
    int: The number of tokens in the prompt.
    """

    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(prompt)

    return len(tokens)


def get_tokens_statistics_from_table_column(source, table_name, column_name, filter, num_rows):
    """
    Retrieves statistics about the tokens in a specified table from a database.
    Args:
        source (str): The source of the database. Either "azure" or "others".
        table_name (str): The name of the table to retrieve data from.
        column_name (str): The name of the column to retrieve data from.
        filter (str): The filter condition to apply to the query. Can be an empty string.
        num_rows (int): The maximum number of rows to retrieve. Set to 0 to retrieve all rows.
    Returns:
        dict: A dictionary containing the statistics of the tokens.
            - source (str): The source of the database. Either "azure" or "others".
            - table_name (str): The name of the table.
            - column_name (str): The name of the column.
            - total_rows (int): The total number of rows retrieved.
            - mean_tokens (float): The mean number of tokens per row.
            - median_tokens (float): The median number of tokens per row.
            - stddev_tokens (float): The standard deviation of the number of tokens per row.
    """
    encoder = tiktoken.get_encoding("cl100k_base")

    conn = get_connection(source)
    cursor = conn.cursor()

    sql = f"""
        select {column_name}
        from {table_name}
        """
    
    if filter:
        sql += f"where {filter} "

    if num_rows > 0:
        sql += f"limit {num_rows};"

    tokens_per_row = []
    cursor.execute(sql)

    for row in cursor:
        tokens = encoder.encode(row[0])
        tokens_per_row.append(len(tokens))
        if num_rows > 0 and len(tokens_per_row) >= num_rows:
            break
        if len(tokens_per_row) % 1000 == 0:
            print(".", end="")

    cursor.close()
    conn.close()
    print("")

    if tokens_per_row:
        mean_tokens = statistics.mean(tokens_per_row)
        median_tokens = statistics.median(tokens_per_row)
        stddev_tokens = statistics.stdev(tokens_per_row) if len(tokens_per_row) > 1 else 0
    else:
        mean_tokens = median_tokens = stddev_tokens = 0

    return {
        'table_name': table_name,
        'column_name': column_name,
        'total_rows': len(tokens_per_row),
        'mean_tokens': round(mean_tokens, 2),
        'median_tokens': round(median_tokens, 2),
        'stddev_tokens': round(stddev_tokens, 2)
    }


def create_and_download_detailed_match_summary(match_id, rows_per_prompt, file_prompt_size, temperature, system_message, tokens, local_folder):
    """
    Generate a summary from a given match ID. The summary is generated by calling the Azure OpenAI API.
    Args:
        match_id (str): The ID of the match.
        rows_per_prompt (int): The number of rows per prompt.
        file_prompt_size (int): The number of prompts per file.
        temperature (float): The temperature value for generating chat completions.
        system_message (str): The system message for generating chat completions.
        tokens (int): The maximum number of tokens for generating chat completions.
        local_folder (str): The local folder to save the generated files.
    Returns:
        None
    """
    start_time = datetime.now()

    num_files_in_batch = 0
    num_file = 0
    in_batch = True
    script = ""

    df = get_json_events_details_from_match_id(match_id)
    count = df.shape[0]

    total_num_files = count // (rows_per_prompt * file_prompt_size)
    if count % (rows_per_prompt * file_prompt_size) > 0:
        total_num_files += 1

    i = 0
    while i < count:
        batch_start_time = datetime.now()
        num_files_in_batch += 1

        df_batch = df.iloc[i:i+rows_per_prompt]
        user_prompt = df_batch.to_string(index=False)

        script += get_chat_completion_from_azure_open_ai(system_message, user_prompt, temperature, tokens)

        duration = datetime.now() - batch_start_time
        time_str = str(duration).split(".")[0]

        now = datetime.now()
        now_str = str(now).split(".")[0]

        print(f"[{now_str}] Batch processing time {num_files_in_batch}/{file_prompt_size}: {time_str} ", end="")

        time = ((datetime.now() - start_time) / (i+1)) * (count - i)
        time_str = str(time).split(".")[0]
        print(f"Estimated remaining time: {time_str}")

        if num_files_in_batch == file_prompt_size:
            num_files_in_batch = 0
            in_batch = False
            num_file += 1

            filename = f"{match_id}-{str(num_file).zfill(6)}-{str(total_num_files).zfill(6)}.txt"
            with open(os.path.join(local_folder, filename), "w", encoding="utf-8") as f:
                f.write(script)

            print(f"  Processed {i+1}/{count} rows. Generated file: {filename}. ")
            script = ""

        i += rows_per_prompt

    if in_batch:
        num_file += 1
        filename = f"{match_id}-{str(num_file).zfill(6)}-{str(total_num_files).zfill(6)}.txt"
        with open(os.path.join(local_folder, filename), "w", encoding="utf-8") as f:
            f.write(script)

        print(f"  Processed {i+1}/{count} rows. Generated file: {filename}. ")
        script = ""

def create_events_summary_per_pk_from_json_rows_in_database(source, tablename, primary_key_column, message_column, match_id, minute, system_message, temperature, tokens):
    """
    Converts JSON data to summary and updates the database with the generated summary.
    Args:
        source (str): The source of the database. Either "azure" or "others".
        tablename (str): The name of the table in the database.
        match_id (int): The ID of the match.
        pk (str): The primary key of the table.
        message_column (str): The name of the column to update.
        system_message (str): The system message.
        temperature (float): The temperature parameter for the OpenAI API.
        tokens (int): The maximum number of tokens for the OpenAI API.
    Returns:
        None: This function does not return any value.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """
    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query=""

        if minute >=0:
            query = sql.SQL(f"""
                SELECT  {primary_key_column} as key, json_ FROM {tablename}
                WHERE match_id = {match_id} 
                and {message_column} IS NULL 
                and minute = {minute}
                ORDER BY {primary_key_column};
            """)
        else:
            query = sql.SQL(f"""
                SELECT  {primary_key_column} as key, json_ FROM {tablename}
                WHERE match_id = {match_id} 
                and {message_column} IS NULL
                ORDER BY {primary_key_column};
            """)

        cursor.execute(query)
        rowCount = cursor.rowcount
        i = 0

        start_time = datetime.now()

        for row in cursor.fetchall():
            i += 1

            row_start_time = datetime.now()

            key = row[0]
            json_ = row[1]
            summary = get_chat_completion_from_azure_open_ai(system_message, json_, temperature, tokens)

            update_query = sql.SQL(f"""
                UPDATE {tablename}
                SET {message_column} = %s
                WHERE match_id = %s
                and {primary_key_column} = %s 
            """)

            cursor.execute(update_query, (summary, match_id, key))
            conn.commit()

            time = datetime.now() - row_start_time
            time_str = str(time).split(".")[0]

            now = datetime.now()
            now_str = str(now).split(".")[0]

            print(f"[{now_str}] Updated primary key {key}, {message_column} column, from match_id {match_id}.", end=" ")
            print(f"Row processing time {i} of {rowCount} row(s), {time_str}.", end=" ")

            time = ((datetime.now() - start_time) / (i+1)) * (rowCount - i)
            time_str = str(time).split(".")[0]

            # add time to now to get the estimated end time
            estimated_end = now + time
            estimated_end_str = str(estimated_end).split(".")[0]
           
            print(f"Estimated remaining time: {time_str} [{estimated_end_str}].")
            
    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}] Error connecting or executing the query in the database.") from e


def create_match_summary(source, tablename, match_id, system_message, temperature, tokens):
    """
    Retrieves the match summary from the specified database table for a given match ID by calling Azure Open AI for summarization.
    Args:
        source (str): The source of the database. Either "azure" or "others".
        tablename (str): The name of the table containing the match summaries.
        match_id (int): The ID of the match for which the summary is requested.
        system_message (str): The content to be used for generating the summary.
        temperature (float): The temperature parameter for generating the summary.
        tokens (int): The maximum number of tokens to use for generating the summary.
    Returns:
        str: The generated match summary.
    Raises:
        Exception: If there is an error connecting to the database or executing the query.
    """
    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT summary FROM {tablename}
            WHERE match_id = {match_id} 
            ORDER BY period, minute
        """)
        cursor.execute(query)
        rowCount = cursor.rowcount
        i = 0

        all_text = ""
        for row in cursor.fetchall():
            all_text += row[0]

        summary = get_chat_completion_from_azure_open_ai(system_message, all_text, temperature, tokens)

        return summary

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}] Error connecting or executing the query in the database.") from e


def search_details_using_embeddings(source, table_name, match_id, search_type, include_lineups, include_json, model, top_n, search_term, system_message, temperature, input_tokens, output_tokens):
    """
    Searches for details using embeddings in the specified source and table.
    Args:
        source (str): The source of the data (e.g., "azure").
        table_name (str): The name of the table to search in.
        match_id (int): The ID of the match to search for.
        search_type (str): The type of search to perform (e.g., "cosine").
        include_lineups (str): Whether to include lineups in the search results (e.g., "yes").
        include_json (str): Whether to include JSON data in the search results (e.g., "no").
        model (str): The model to use for embeddings (e.g., "text-embedding-3-small").
        top_n (int): The number of results to return.
        search_term (str): The search term to use.
        system_message (str): The system message to include in the prompt.
        temperature (float): The temperature for generating completions.
        input_tokens (int): The maximum number of input tokens allowed.
        output_tokens (int): The maximum number of output tokens allowed.
    Returns:
        tuple: A tuple containing the prompt and the summary of the search results.
    """

    try:

        column_name = ""
        model_name = ""

        if model=="" or model=="text-embedding-3-small":
            column_name = "summary_embedding_t3_small"
            model_name = "text-embedding-3-small"
        if model=="text-embedding-3-large":
            column_name = "summary_embedding_t3_large"
            model_name = "text-embedding-3-large"

        if isinstance(input_tokens, str):
            if not input_tokens.isdigit():
                input_tokens = 10000
            input_tokens = int(input_tokens)

        if isinstance(output_tokens, str):
            if not output_tokens.isdigit():
                output_tokens = 5000
            output_tokens = int(output_tokens)

        # if top_s is string convert to int
        if isinstance(top_n, str):
            # if top_n is not a number set to 10
            if not top_n.isdigit():
                top_n = 10
            top_n = int(top_n)

        if isinstance(top_n, float):
            top_n = int(top_n)

        if int(top_n) < 1:
            top_n = 10

        if include_json.lower() =="":
            include_json = "no"
        if include_json.lower() != "no":
            include_json = "yes"            

        # if cosine similarity set var k = "=" else "#"
        k_search = "#"
        if search_type.lower() == "cosine":
            k_search = "="
        if search_type.lower() == "innerp":
            k_search = "#"

        conn = get_connection(source)
        cursor = conn.cursor()

        summary = "summary"
        if include_json.lower() == "yes":
            summary = "json_"        

        query = sql.SQL(f"""
            SELECT id, {summary}
            FROM {table_name} 
            WHERE match_id = {match_id}
            ORDER BY {column_name} <{k_search}> azure_openai.create_embeddings('{model_name}', '{search_term}')::vector
            LIMIT {top_n};
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "I have not found rows that matches in the database.", "NONE. I cannot find an answer. Please refine the question."

        # convertir el resultado a un pandas dataframe
        df1 = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

        # obtener array de los identificadores de la primera columna
        ids = df1['id'].values
        extended_ids = []

        # para cada numero en ids
        for i in ids:
            extended_ids.append(i-1)
            extended_ids.append(i+1)

        # remove duplicates and order by id
        ids = list(set(extended_ids))
        ids.sort()

        # añadir al df la llamada a una función que recupere los identificadores
        df2 = get_dataframe_from_ids(source, table_name, summary, ids)

        # Concatenar los dataframes
        df = pd.concat([df1, df2], ignore_index=True)
        df = df.drop_duplicates(subset='id', keep='first')
        df = df.sort_values(by='id')
        # remofe the id column from df
        df = df.drop(columns=['id'])

        prompt=""
        prompt += f"### EVENTS\n" + df.to_string(index=False, justify='left')

        d_game_result = get_game_result_data(source, match_id)
        prompt += f"\n\n### GAME RESULT\n" + d_game_result

        if include_lineups.lower() == "yes":
            d_game_players = get_game_players_data(source, match_id)
            prompt += f"\n\n### GAME PLAYERS\n" + d_game_players

        prompt += f"\n\n### PROMPT\n{search_term}"

        tokens = count_tokens(prompt)

        summary = ""
        if tokens > input_tokens:
            summary = "TOKENS. The prompt is too long. Please try a shorter query."
        else:
            summary = get_chat_completion_from_azure_open_ai(system_message, prompt, temperature, output_tokens)

        return prompt, summary

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}] Error connecting or executing the query in the database.") from e


def get_dataframe_from_ids(source, table_name, summary, ids):

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        # convertir array de ids a string de numeros separado por comas
        ids_str = ','.join(map(str, ids))

        query = sql.SQL(f"""
            SELECT id, {summary}
            FROM {table_name}
            WHERE id IN ({ids_str});
        """)
        cursor.execute(query)        

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        return df

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}] Error connecting or executing the query in the database.") from e


def process_prompt_from_web (match_id, model, \
                             search_type, top_n, include_lineups, influence_temperature, \
                             system_message, question, input_tokens, output_tokens):

    if include_lineups.lower() != "no":
        include_lineups = "yes"

    temperature = 0.0
    if influence_temperature == "":
        temperature = 0.1
    else:
        try:
            temperature = float(influence_temperature)
        except ValueError:
            temperature = 0.1

    include_json = "no"

    dataframe, summary = search_details_using_embeddings ("Azure", "events_details__quarter_minute", match_id, search_type, 
                                                            include_lineups, include_json, model,
                                                            top_n, question, system_message, temperature, input_tokens, output_tokens)

    return dataframe, summary

def process_prompt (questions, match_id, system_message, input_tokens, output_tokens, local_folder):
    """
    Process tokens and perform search using embeddings.
    Args:
        questions (list): List of dictionaries containing questions to be processed.
        match_id (str): ID of the match.
        system_message (str): System message.
        input_tokens (list): List of input tokens.
        output_tokens (list): List of output tokens.
        local_folder (str): Local folder path.
    Returns:
        None
    """

     # iterate over the questions and print each column
    for question in questions:
        question_number = question["question_number"]
        search_type = question["search_type"]
        top_n = question["top_n"]
        search_term = question["question"]
        include_lineups = question.get("include_lineups", "")
        influence_temperature = question.get("temperature", "")

        if include_lineups.lower() != "no":
            include_lineups = "yes"

        temperature = 0.0
        if influence_temperature == "":
            temperature = 0.1
        else:
            try:
                temperature = float(influence_temperature)
            except ValueError:
                temperature = 0.1

        include_json = question.get("include_json", "")
        if include_json.lower() =="":
            include_json = "no"
        if include_json.lower() != "no":
            include_json = "yes"

        model = question.get("model", "")

        dataframe, summary = search_details_using_embeddings ("Azure", "events_details__quarter_minute", match_id, search_type, 
                                                              include_lineups, include_json, model,
                                                              top_n, search_term, system_message, temperature, input_tokens, output_tokens)
        print(f"Question: {question_number} - {search_term}")
        print(f"Answer: {summary}")
        print(f"------------------------------------------------------------------------")

        export_script_result_to_text(dataframe, summary, match_id, system_message, search_term, local_folder, question_number + "_" + search_type)

def export_script_result_to_text(dataframe, match_id, system_message, summary, search_term, local_folder, filename):
    """
    Export the script result to a text file.
    Parameters:
    - local_folder (str): The folder path where the text file will be saved.
    - summary (str): The summary of the script result.
    - filename (str): The name of the text file.
    Returns:
    None
    """

    now = datetime.now()
    sc = int(now.strftime("%S"))
    ms = int(now.strftime("%f"))
    v = sc * ms
    v = str(v) + "_"

    tag ="-"
    if summary.startswith("NONE"):
        tag = "_NONE_"
    if summary.startswith("TOKENS"):
        tag = "_TOKENS_"
    if summary.startswith("NONE"):
        tag = "_NONE_"

    folder = os.path.join(local_folder, "scripts_summary", "Answers")
    filename += tag + v + ".txt"

    text = ""
    text  = f"## SYSTEM MESSAGE\n"
    text += f"       {system_message}.\n\n"

    text += f"## SEARCH TERM\n"
    text += f"       {search_term}.\n\n"

    text += f"## MATCH ID\n"
    text += f"       {match_id}.\n\n"

    text += f"## ANSWER\n"
    text += f"\n\n{summary}.\n"

    text += f"## DATA FRAME\n"

    text += dataframe
    
    with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
        f.write(text)
