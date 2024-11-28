import os
import tiktoken
import statistics
import urllib
import sqlite3 as sqllib3
import pandas as pd
from openai import AzureOpenAI
import datetime
from datetime import datetime
import traceback
import pyodbc
import psycopg2
from sqlalchemy import create_engine
from module_data import get_game_result_data, get_game_players_data, get_json_events_details_from_match_id, get_dynamic_sql

def decode_source(source):

    if source.lower() == "postgres" or source.lower() == "postgresql" or source.lower() == "azure-postgres" or source.lower() == "azure-postgresql":
        return "azure-postgres"

    if source.lower() == "azuresql" or source.lower() == "sqlazure" or source.lower() == "azure-sql" or source.lower() == "sql-azure":
        return "azure-sql"

    if source.lower() == "sqlite" or source.lower() == "local" or source.lower() == "sqlite-local":
        return "sqlite-local"


def get_connection_pyodbc(source):

    source = decode_source(source)
    
    conn = None

    if source == "azure-postgres":

        conn = psycopg2.connect(
            host=os.getenv('DB_SERVER_AZURE_POSTGRES'),
            database=os.getenv('DB_NAME_AZURE_POSTGRES'),
            user=os.getenv('DB_USER_AZURE_POSTGRES'),
            password=os.getenv('DB_PASSWORD_AZURE_POSTGRES')
        )    

    if source == "azure-sql":
        server = os.getenv('DB_SERVER_AZURE')
        database = os.getenv('DB_NAME_AZURE')
        username = os.getenv('DB_USER_AZURE')
        password = os.getenv('DB_PASSWORD_AZURE')
        driver = '{ODBC Driver 18 for SQL Server}'

        connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        # Connect to the Azure database
        conn = pyodbc.connect(connection_string)

    if source == "sqlite-local":
        conn = sqllib3.connect('rag_challenge.db')

    return conn


def get_connection(source):

    source = decode_source(source)
    
    engine = None

    if source == "azure-postgres":
    
        # Crea el URI de conexión para PostgreSQL en Azure
        db_user = os.getenv('DB_USER_AZURE_POSTGRES')
        db_password = os.getenv('DB_PASSWORD_AZURE_POSTGRES')
        db_host = os.getenv('DB_SERVER_AZURE_POSTGRES')
        db_name = os.getenv('DB_NAME_AZURE_POSTGRES')
        db_password = urllib.parse.quote_plus(db_password)
        
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
        engine = create_engine(connection_string)

    elif source == "azure-sql":
        # Crea el URI de conexión para Azure SQL con ODBC
        server = os.getenv('DB_SERVER_AZURE')
        database = os.getenv('DB_NAME_AZURE')
        username = os.getenv('DB_USER_AZURE')
        password = os.getenv('DB_PASSWORD_AZURE')
        password = urllib.parse.quote_plus(password)

        # Usando pyodbc para generar la cadena de conexión adecuada
        connection_string = (
            f"mssql+pyodbc://{username}:{password}@{server}/{database}"
            "?driver=ODBC+Driver+18+for+SQL+Server"
        )
        engine = create_engine(connection_string)

    elif source == "sqlite-local":
        # Para SQLite
        engine = create_engine('sqlite:///rag_challenge.db')

    return engine


def get_chat_completion_from_azure_open_ai(system_message, user_prompt, temperature, tokens, model2 = False):
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

    if model2:
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL2'),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=tokens,
        )
    else:
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
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
        table_name (str): The name of the table to retrieve data from.
        column_name (str): The name of the column to retrieve data from.
        filter (str): The filter condition to apply to the query. Can be an empty string.
        num_rows (int): The maximum number of rows to retrieve. Set to 0 to retrieve all rows.
    Returns:
        dict: A dictionary containing the statistics of the tokens.
            - source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
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


def create_and_download_detailed_match_summary(source, match_id, rows_per_prompt, file_prompt_size, temperature, system_message, tokens, local_folder):
    """
    Generate a summary from a given match ID. The summary is generated by calling the Azure OpenAI API.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
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

    df = get_json_events_details_from_match_id(source, match_id)
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


def create_match_summary(source, tablename, match_id, system_message, temperature, tokens):
    """
    Retrieves the match summary from the specified database table for a given match ID by calling Azure Open AI for summarization.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
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

        query = f"""
            SELECT summary FROM {tablename}
            WHERE match_id = {match_id} 
            ORDER BY period, minute
        """

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
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def search_details_using_embeddings(source, match_id, add_match_info, \
                                    language, search_type, embeddings_model, \
                                    system_message, search_term, \
                                    top_n, temperature, input_tokens, output_tokens):
    """
    Searches for details using embeddings in the specified source and table.
    Args:
        source (str): The source of the data (e.g., "azuresql").
        match_id (int): The ID of the match to search for.
        add_match_info (str): Whether to include match information in the search (e.g., "yes").
        language (str): language used for the search
        search_type (str): The type of search to perform (e.g., "cosine").
        embeddings_model (str): The model to use for embeddings (e.g., "text-embedding-3-small").
        system_message (str): The system message to include in the prompt.
        search_term (str): The search term to use.
        top_n (int): The number of results to return.
        temperature (float): The temperature for generating completions.
        input_tokens (int): The maximum number of input tokens allowed.
        output_tokens (int): The maximum number of output tokens allowed.
    Returns:
        search_term: The search term used in the search (translated to english).
        tuple: A tuple containing the prompt and the summary of the search results.
    """

    try:

        if language != "english":
            search_term = get_chat_completion_from_azure_open_ai(  \
                f"TRANSLATE the text below from [{language}] to [english]: ", search_term, 0.1, 5000)
        
        column_name_postgres = ""
        column_name_sql = ""
        model_name = ""
        extension = "azure_openai"
        search_type = search_type.lower()

        if embeddings_model=="" or embeddings_model=="text-embedding-3-small":
            column_name_postgres = "summary_embedding_t3_small"
            column_name_sql = "embedding_3_small"
            model_name = "text-embedding-3-small"
        if embeddings_model=="text-embedding-ada-002":
            column_name_postgres = "summary_embedding_ada_002"
            column_name_sql = "embedding_ada_002"
            model_name = "text-embedding-ada-002"
        if embeddings_model=="text-embedding-3-large":
            column_name_postgres = "summary_embedding_t3_large"
            column_name_sql = ""
            model_name = "text-embedding-3-large"
        if embeddings_model=="multilingual-e5-small:v1":
            column_name_postgres = "summary_embedding"
            column_name_sql = ""
            model_name = "multilingual-e5-small:v1"
            extension = "azure_local_ai"

        if isinstance(input_tokens, str):
            if not input_tokens.isdigit():
                input_tokens = 10000
            input_tokens = int(input_tokens)

        if isinstance(output_tokens, str):
            if not output_tokens.isdigit():
                output_tokens = 5000
            output_tokens = int(output_tokens)

        # if top_s is string convert to int
        top_n = 10
        if isinstance(top_n, str):
            # if top_n is not a number set to 10
            if not top_n.isdigit():
                top_n = 10
            top_n = int(top_n)

        if isinstance(top_n, float):
            top_n = int(top_n)

        if int(top_n) < 1:
            top_n = 10

        include_json = "no"
        if include_json.lower() =="":
            include_json = "no"
        if include_json.lower() != "no":
            include_json = "yes"            

        k_search = "#"
        k_search_sqlazure = "cosine"
        order_by = " ASC"
        if search_type == "cosine":
            k_search = "="
            k_search_sqlazure = "cosine"
            order_by = " ASC"
        if search_type == "negative inner product - dot":
            k_search = "#"
            k_search_sqlazure = "dot"
            order_by = " DESC"
        if search_type == "l1 - manhattan":
            k_search = "+"
            order_by = " ASC"
        if search_type == "l2 - euclidean":
            k_search = "-"
            k_search_sqlazure = "euclidean"
            order_by = " ASC"

        summary = "summary"
        if include_json.lower() == "yes":
            summary = "json_"        

        conn = get_connection(source)

        query = ""
        table_name = "events_details__quarter_minute"

        if source == "azure-postgres":
            table_name = "events_details__quarter_minute"
            query = f"""
                SELECT id, {summary}
                FROM {table_name} 
                WHERE match_id = {match_id}
                ORDER BY {column_name_postgres} <{k_search}> {extension}.create_embeddings('{model_name}', '{search_term}')::vector {order_by}
                LIMIT {top_n};
            """

        if source == "azure-sql":
            table_name = "events_details__15secs_agg"
            query = f"""
                DECLARE @e VECTOR(1536);
                EXEC dbo.get_embeddings @model = '{model_name}', @text = '{search_term}', @embedding = @e OUTPUT;

                SELECT TOP {top_n} id, {summary}
                    , VECTOR_DISTANCE ('{k_search_sqlazure}', @e, {column_name_sql}) AS Distance
                FROM {table_name} 
                WHERE match_id = {match_id}
                ORDER BY Distance {order_by};
            """

        df1 = pd.read_sql(query, conn)
        rowCount = df1.shape[0]

        if rowCount == 0:
            return "I have not found rows that matches in the database.", "NONE. I cannot find an answer. Please refine the question."

        # get the ids from the seach (id is the primary key)
        ids = df1['id'].values
        extended_ids = []

        # for each id, add the previous and next id
        for i in ids:
            extended_ids.append(i-1)
            extended_ids.append(i+1)

        # remove duplicates and order by id
        ids = list(set(extended_ids))
        ids.sort()

        # add to the dataframe the previous and next rows
        df2 = get_dataframe_from_ids(source, table_name, summary, ids)

        # concatenate results
        df = pd.concat([df1, df2], ignore_index=True)
        df = df.drop_duplicates(subset='id', keep='first')
        df = df.sort_values(by='id')
        # remove the id column from df
        df = df.drop(columns=['id'])
        # the query from postgre do not includes the Distance as a column
        if source == "azure-sql":
            df = df.drop(columns=['Distance'])
        
        enriched_system_message = ""
        df_str = df.to_string(index=False)
        # remove double spaces
        df_str = df_str.replace("  ", " ")
        enriched_system_message += f"### EVENTS\n" + df_str

        if add_match_info.lower() == "yes":
            d_match_info = get_game_result_data(source, match_id)
            # remove double spaces
            d_match_info = d_match_info.replace("  ", " ")
            enriched_system_message += f"\n\n### GAME_RESULT\n" + d_match_info

        enriched_system_message += f"----------------------------------\n\n{system_message}"

        tokens = count_tokens(enriched_system_message)

        summary = ""
        if tokens > input_tokens:
            summary = "TOKENS. The prompt is too long. Please try a shorter query."
        else:
            summary = get_chat_completion_from_azure_open_ai(enriched_system_message, search_term, temperature, output_tokens)

        return search_term, summary

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def search_dynamic_query(source, db_schema, language, search_term, \
                temperature, output_tokens):
    """
    Searches for details using embeddings in the specified source and table.
    Args:
        source (str): The source of the data (e.g., "azuresql").
        language (str): language used for the search
        search_term (str): The search term to use.
        temperature (float): The temperature for generating completions.
        output_tokens (int): The maximum number of output tokens allowed.
    Returns:
        string: the SQL query.
        tuple2: the resultset.
    """

    sql_query = ""
    try:

        system_message = f"""
        Given the following database schema:
        #####
         {str(db_schema)}
        #####
        Provide a SQL query to execute in a database to answer the USER QUESTION.
        TAG the query between ###. For example: ###SELECT column1, column2 FROM schema.table_name;###
        Do not use indentation in the query.
        Use only the column names and table names from the schema provided at the top between #####.
        Never invent column names or table names.
        """

        if language != "english":
            search_term = get_chat_completion_from_azure_open_ai(  \
                "translate the following text to ENGLISH: ", search_term, 0.1, 5000)

        if isinstance(output_tokens, str):
            if not output_tokens.isdigit():
                output_tokens = 5000
            output_tokens = int(output_tokens)

        sql_query = get_chat_completion_from_azure_open_ai(system_message, search_term, temperature, output_tokens)

        # extract the query from the response
        sql_query = sql_query.split("###")[1]

        # if sql_query is empty, return an error
        if sql_query == "":
            return "NONE: I cannot build a SQL query.", "SQL Query is empty. Please refine the question."
        
        result = get_dynamic_sql (source, sql_query, as_data_frame=True)

        return sql_query, result
    
        #### removed post-formating

        system_message = f"""
        Given the following result set:
        ###
         {str(result)}
        ###
        """        

        result = get_chat_completion_from_azure_open_ai(system_message, "format the result set in markdown", temperature, output_tokens)
        return sql_query, result

    except Exception as e:
        raise e
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database. query [{sql_query}]") from e



def get_random_dataframe_from_match_id(source, table_name, summary, match_id, num_rows):
    """    
    Retrieves a random DataFrame from a database based on a match_id.
    Args:
        source (str): The source identifier for the database connection.
        table_name (str): The name of the table to query.
        summary (str): The column(s) to retrieve from the table.
        match_id (int): The ID of the match to retrieve data from.
    Returns:
        pd.DataFrame: A DataFrame containing the results of the query.
    Raises:
        RuntimeError: If there is an error connecting to the database or executing the query.
    """
    try:

        conn = get_connection(source)

        query = f"""
            SELECT TOP ({num_rows}) {summary}
            FROM {table_name}
            WHERE match_id = {match_id}
            ORDER BY NEWID();
        """
        
        df = pd.read_sql(query, conn)
        return df

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_dataframe_from_ids(source, table_name, summary, ids):
    """    
    Retrieves a DataFrame from a database based on a list of IDs.
    Args:
        source (str): The source identifier for the database connection.
        table_name (str): The name of the table to query.
        summary (str): The column(s) to retrieve from the table.
        ids (list): A list of IDs to filter the query.
    Returns:
        pd.DataFrame: A DataFrame containing the results of the query.
    Raises:
        RuntimeError: If there is an error connecting to the database or executing the query.
    """
    try:

        conn = get_connection(source)

        # convertir array de ids a string de numeros separado por comas
        ids_str = ','.join(map(str, ids))

        query = f"""
            SELECT id, {summary}
            FROM {table_name}
            WHERE id IN ({ids_str});
        """
        
        df = pd.read_sql(query, conn)
        return df

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def process_prompt_from_questions_batch (source, language, questions, match_id, embeddings_model, system_message, input_tokens, output_tokens, local_folder, export_results = True):
    """
    process each question in the array with the appropiate parameters.
    the questions array includes properties that influence in the search process like temperature, top_n, search_type, model, add_match_info
    Args:
        source (str): The source of the data (e.g., "azure-sql").
        language (str): language from the prompt
        questions (arraylist): List of dictionaries containing questions to be processed.
        match_id (str): ID of the match.
        embeddings_model (str): The model to use for embeddings (e.g., "text-embedding-3-small").
        system_message (str): System message.
        input_tokens (int): input tokens.
        output_tokens (int): output tokens.
        local_folder (str): Local folder path.
    Returns:
        None
    """

    source = decode_source(source)

     # iterate over the questions and print each column
    for question in questions:
        question_number = question["question_number"]
        add_match_info = question.get("add_match_info", "yes")
        influence_temperature = question.get("temperature", 0.15)
        top_n = question["top_n"]
        search_type = question["search_type"]
        search_term = question["question"]

        if language != "english":
            search_term = get_chat_completion_from_azure_open_ai(  \
                "translate the following text to ENGLISH: ", search_term, 0.1, 5000)

        if add_match_info.lower() != "no":
            add_match_info = "yes"

        temperature = 0.0
        if influence_temperature == "":
            temperature = 0.15
        else:
            try:
                temperature = float(influence_temperature)
            except ValueError:
                temperature = 0.15

        error=""
        try:
            dataset, summary = search_details_using_embeddings (source, match_id, add_match_info, 
                                                            language, search_type, embeddings_model, 
                                                            system_message, search_term, 
                                                            top_n, temperature, input_tokens, output_tokens)

        except Exception as e:
            error = f"ERROR: {str(e)}"

        if not error:

            print(f"Question : {question_number} - {search_term}")
            print(f"Answer   : {summary}")
            print(f"------------------------------------------------------------------------")

            if export_results:

                error =""
                if summary.startswith("NONE"):
                    error = "None"
                if summary.startswith("TOKENS"):
                    error = "Tokens"

                yaml = ""
                yaml += f"  - question_number: {question_number}\n"
                yaml += f"    search_type: {search_type}\n"
                yaml += f"    embeddings_model: {embeddings_model}\n"
                yaml += f"    add_match_info: {add_match_info}\n"
                yaml += f"    temperature: {temperature}\n"
                yaml += f"    top_n: {top_n}\n"
                yaml += f"    search_term: {search_term}\n"
                yaml += f"    error_category: {error}\n"
                yaml += f"    system_message: {system_message}\n"
                yaml += f"    summary: |\n"
                yaml += '\n'.join([f"      {line}" for line in summary.splitlines()]) + "\n"
                yaml += f"    dataframe: |\n"
                yaml += '\n'.join([f"      {line}" for line in dataset.splitlines()])

                filename = f"{question_number}_{match_id}_{search_type}_{source}_"
                if error:
                    filename += f"{error}_"

                export_script_result_to_yaml(yaml, local_folder, filename)


def export_script_result_to_yaml(yaml, local_folder, filename):
    """
    Export the script result to a text file.
    Parameters:
    . yaml (str): The YAML text to be saved.
    - local_folder (str): The folder path where the text file will be saved.
    - filename (str): The name of the text file.
    Returns:
    None
    """

    now = datetime.now()
    sc = int(now.strftime("%S"))
    ms = int(now.strftime("%f"))
    ts = sc * ms
    ts = "_" + str(ts)
    filename += ts + ".yaml"

    folder = os.path.join(local_folder, "scripts_summary", "Answers")
    # Crear carpeta local recursivamente si no existe
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, filename), "w", encoding="utf-8") as f:
        f.write(yaml)

