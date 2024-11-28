import os
import urllib
import json
import traceback
import pandas as pd
import sqlite3 as sqllib3
import pyodbc
import psycopg2
from sqlalchemy import create_engine
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

        # tries to conect to the server to warm up [for sql azure serverless]
        try:
            df = pd.read_sql("SELECT @@servername", engine)
        except Exception as e:
            try:
                df = pd.read_sql("SELECT @@servername", engine)
            except Exception as e:
                raise RuntimeError(f"Error connecting to the Azure SQL database.") from e

    elif source == "sqlite-local":
        # Para SQLite
        engine = create_engine('sqlite:///rag_challenge.db')

    return engine


def copy_data_between_sql_sources(source, destination, table_name, columns_list, filter_predicate="", match_id=-1):
    """
    Connects to a local database and copies tables to destination database.
    This function facilitates the migration of data between databases, allowing for seamless transfer
    of information from a local environment to a cloud-based service such as Azure.

    THIS METHOD IS NOT USED IN THE CURRENT IMPLEMENTATION
    IT WAS VALID FOR TESTING WHEN LOADING THE DATA IN A LOCAL DATABASE AND THEN MOVE TO SQL AZURE

    Parameters:
    - source (str): The source database to copy data from (e.g., 'local' or 'azuresql').
    - destination (str): The destination database to copy data to (e.g., 'local' or 'azuresql').
    - table_name (str): The name of the table to copy data from the local database to the Azure database.
    - column_list (str): A list of column names to copy from the local table to the Azure table.
    - filter_predicate (str): A filter predicate to apply when selecting data from the local table.
    - match_id (int): The ID of the match to copy data for. If <= 0, all data from the table will be copied.

    Functionality:
    - Database Connection: Establishes connections to the local and Azure SQL Server databases using provided credentials.
    - Data Transfer: Copies data from specified tables in the local database to corresponding tables in the Azure database.
    - Transaction Management: Ensures data integrity by committing changes to the Azure database after successful data transfer.
    - Error Handling: Provides detailed error messages in case of connection issues or data transfer failures.

    Output:
    - Console Output: Provides feedback on the data transfer process, including the number of rows copied and any errors encountered.
    - Database Update: Updates the specified tables in the Azure SQL Server database with data from the local database.
    """

    try:
        conn_src = get_connection_pyodbc(source)
        cursor_src = conn_src.cursor()

        conn_dest = get_connection_pyodbc(destination)
        cursor_dest = conn_dest.cursor()

        # Count total rows to be copied
        count_query = ""
        if filter_predicate:
            count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {filter_predicate};"
        else:
            if match_id <= 0:
                count_query = f"SELECT COUNT(*) FROM {table_name};"
            else:
                count_query = f"SELECT COUNT(*) FROM {table_name} WHERE match_id = {match_id};"
        
        cursor_src.execute(count_query)
        total_rows = cursor_src.fetchone()[0]
        print(f"Total rows to be copied: {total_rows}")

        select_query=""
        # if match_id <= 0, then copy all data from the table
        if filter_predicate:
            # Query to select all data from the table
            select_query = f"""SELECT {columns_list} FROM {table_name} WHERE {filter_predicate};"""
        else:
            if match_id <= 0:
                # Query to select all data from the table
                select_query = f"""SELECT {columns_list} FROM {table_name};"""
            else:
                # Query to select all data from the table
                select_query = f"""SELECT {columns_list} FROM {table_name} WHERE match_id = {match_id};"""

        cursor_src.execute(select_query)

        # Fetch rows in batches to avoid loading everything into memory
        batch_size = 100
        rows = cursor_src.fetchmany(batch_size)
        total_rows_copied = 0

        while rows:
            for row in rows:
                insert_query = f"""
                    INSERT INTO {table_name} ({columns_list})
                    VALUES ({', '.join(['?' for _ in range(len(row))])})
                """

                # Execute the INSERT query
                cursor_dest.execute(insert_query, row)
                conn_dest.commit()

                total_rows_copied += 1

                # Print progress for every 10 rows copied
                if total_rows_copied % 10 == 0:
                    print(f"{total_rows_copied} of {total_rows} rows copied from {source} to {destination}. Table name: [{table_name}].")

            # Fetch next batch of rows
            rows = cursor_src.fetchmany(batch_size)

        # Print final summary
        print(f"Data transfer complete. Total rows copied: {total_rows_copied}")

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e

    finally:
        # Ensure that connections are closed properly
        if cursor_src:
            cursor_src.close()
        if conn_src:
            conn_src.close()
        if cursor_dest:
            cursor_dest.close()
        if conn_dest:
            conn_dest.close()


def load_lineups_data_into_database(source, local_folder):
    """
    Connects to a SQL Server database and imports lineup data from JSON files into specified database tables.
    Processes each JSON file, extracting relevant team and player information, and performs SQL insert operations
    to store this data in the database. Designed to handle batch processing of multiple files and provides options
    for interactive user control over the execution.

    Parameters:
    - source (str): The source of the database. Either "azure-sql", "azure-postgres", or "sqlite-local".
    - local_folder (str): The directory path where the lineup JSON files are stored.

    Functionality:
    - Database Connection: Establishes a connection to the SQL Server database using provided credentials.
    - File Processing: Iterates over JSON files in the specified directory, processing each file that matches the `.json` extension.
    - Data Extraction and Insertion:
      - Extracts the match ID and team information for each file.
      - Constructs and executes SQL queries to insert data into the 'lineups' table.
      - Processes each player's data within the teams to insert into the 'players' table.
    - User Interaction: Optionally prompts the user for confirmation before processing files if the `interactive` parameter is True.
    - Commit and Close: Commits the transactions to the database and closes the connection.

    Output:
    - Console Output: Provides feedback on the number of files processed, and outputs a message each time data for a match is successfully inserted into the database.
    - Database Update: Updates the 'lineups' and 'players' tables in the database with new data from the processed JSON files.
    """

    # Connect to the database
    conn = get_connection_pyodbc(source)
    cursor = conn.cursor()
    # events files

    eventsPath = os.path.join(local_folder, 'lineups')

    for root, dirs, files in os.walk(eventsPath):

        # Print the number of files to process
        # Ask the user for confirmation to proceed
        print(f"Processing {len(files)} [lineups] files...")
        print("---------------------------------------------")

        i=0

        for file in files:
            i+=1

            if file.endswith(".json"):

                # The file name is the match_id, example: 134141.json (according to the docs)
                match_id = file.replace('.json', '')

                # Check if the match_id already exists in the matches table
                sql = f"SELECT COUNT(*) FROM lineups WHERE match_id = '{match_id}'"
                cursor.execute(sql)
                count = cursor.fetchone()[0]

                # if it already exists, skip the file
                if count > 0:
                    print(f"Events ({i}/{len(files)}). The match_id [{match_id}] already exists in the lineups table. Skipping file...")
                    continue

                with open(os.path.join(eventsPath, file), 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)

                sql = """
                    INSERT INTO lineups (
                        match_id, 
                        home_team_id, home_team_name, 
                        away_team_id, away_team_name,
                        json_
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """

                # Query parameters
                params = (
                    match_id,
                    data[0]['team_id'], data[0]['team_name'].replace("'", "''"),
                    data[1]['team_id'], data[1]['team_name'].replace("'", "''"),
                    json.dumps(data).replace("'", "''")  # Escape single quotes in JSON
                )

                # Execute the SQL query with parameters
                cursor.execute(sql, params)

                # Insert players into the players table
                sql_player = """
                    INSERT INTO players (
                        match_id, team_id, team_name, player_id, player_name, jersey_number,
                        country_id, country_name,
                        position_id, position_name,
                        from_time, to_time, from_period, to_period,
                        start_reason, end_reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                # Function to insert players
                def insert_players(team_id, team_name, players):
                    for player in players:
                        # Check if positions are available
                        if player.get('positions'):
                            position = player['positions'][0]
                            position_id = position.get('position_id', None)
                            position_name = position.get('position', '').replace("'", "''")
                            from_time = position.get('from', None)
                            to_time = position.get('to', None)
                            from_period = position.get('from_period', None)
                            to_period = position.get('to_period', None)
                            start_reason = position.get('start_reason', '').replace("'", "''")
                            end_reason = position.get('end_reason', '').replace("'", "''")
                        else:
                            # Valores por defecto si no hay posiciones
                            position_id = None
                            position_name = ''
                            from_time = None
                            to_time = None
                            from_period = None
                            to_period = None
                            start_reason = ''
                            end_reason = ''

                        # Verificación de la información de 'country' del jugador
                        country_id = player.get('country', {}).get('id', None)
                        country_name = player.get('country', {}).get('name', '').replace("'", "''") if player.get('country') else ''

                        params_player = (
                            match_id, 
                            team_id,
                            team_name.replace("'", "''"),
                            player['player_id'],
                            player['player_name'].replace("'", "''"),
                            player['jersey_number'],
                            country_id,
                            country_name,
                            position_id,
                            position_name,
                            from_time,
                            to_time,
                            from_period,
                            to_period,
                            start_reason,
                            end_reason
                        )
                        cursor.execute(sql_player, params_player)

                insert_players(data[0]['team_id'], data[0]['team_name'], data[0]['lineup'])
                insert_players(data[1]['team_id'], data[1]['team_name'], data[1]['lineup'])

                conn.commit()

                print(f"Lineups ({i}/{len(files)}). Inserted data for match_id {match_id} into [lineups] and [players] tables: [{data[0]['team_name']}] - [{data[1]['team_name']}].")

    # Close the connection
    cursor.close()
    conn.close()


def load_events_data_into_database(source, local_folder):
    """
    Connects to a SQL Server database and imports event data from JSON files into specified database tables.
    This function processes event files, extracting detailed event information, and performs SQL insert operations
    to store this data in the database. It is capable of handling batch processing of multiple files and includes
    an interactive mode for user control over the execution process.

    Parameters:
    - source (str): The source of the database. Either "azure-sql", "azure-postgres", or "sqlite-local".
    - local_folder (str): The directory path where the event JSON files are stored.

    Functionality:
    - Database Connection: Establishes a connection to the SQL Server database using provided credentials.
    - File Processing: Iterates over JSON files in the specified directory, processing each file that ends with `.json`.
    - Data Extraction and Insertion:
      - Checks if the match ID from the filename already exists in the database to avoid duplicates.
      - For new entries, extracts detailed event data from each file and constructs SQL queries to insert this data into 'events' and 'events_details' tables.
    - User Interaction: Optionally prompts the user for confirmation before processing files if the `interactive` parameter is set to True.
    - Commit and Close: Commits the transactions to the database and closes the connection after all files are processed or upon user cancellation.

    Output:
    - Console Output: Provides feedback on the number of files processed and details about the data inserted, such as the number of events processed for each file.
    - Database Update: Updates the 'events' and 'events_details' tables in the database with new data from the processed JSON files.
    """
        # Connect to the database
    conn = get_connection_pyodbc(source)
    cursor = conn.cursor()

    # Path to the events files
    eventsPath = os.path.join(local_folder, 'events')

    for root, dirs, files in os.walk(eventsPath):

        # Print the number of files to process
        # Ask the user for confirmation to proceed
        print(f"Processing {len(files)} [Events] files...")
        print("---------------------------------------------")

        i = 0

        for file in files:

            i += 1

            if file.endswith(".json"):

                # The file name is the match_id, like 134141.json (according to the documentation)
                match_id = file.replace('.json', '')

                # Check if the match_id already exists in the matches table
                sql = f"SELECT COUNT(*) FROM events WHERE match_id = '{match_id}'"
                cursor.execute(sql)
                count = cursor.fetchone()[0]

                # if it already exists, skip the file
                if count > 0:
                    print(f"Events ({i}/{len(files)}). The match_id [{match_id}] already exists in the events table. Skipping file...")
                    continue

                with open(os.path.join(eventsPath, file), 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)

                sql = """
                    INSERT INTO events (
                        match_id, json_
                    )
                    VALUES (?, ?)
                """

                # Extract the necessary data from the event
                params = (
                    match_id,
                    json.dumps(data).replace("'", "''")  # Escape single quotes in JSON
                )                

                # Execute the SQL query with parameters
                cursor.execute(sql, params)

                # split the data from events into events_details based on the jsonb_array_elements function
                sql = """INSERT INTO events_details (
                    match_id,
                    id_guid,
                    index_,
                    period,
                    timestamp,
                    minute,
                    second,
                    type_id,
                    type,
                    possession,
                    possession_team_id,
                    possession_team,
                    play_pattern_id,
                    play_pattern,
                    json_
                )
                SELECT
                    ? AS match_id,
                    JSON_VALUE(value, '$.id') AS id_guid,
                    CAST(JSON_VALUE(value, '$.index') AS INT) AS index_,
                    CAST(JSON_VALUE(value, '$.period') AS INT) AS period,
                    JSON_VALUE(value, '$.timestamp') AS timestamp,
                    CAST(JSON_VALUE(value, '$.minute') AS INT) AS minute,
                    CAST(JSON_VALUE(value, '$.second') AS INT) AS second,
                    CAST(JSON_VALUE(value, '$.type.id') AS INT) AS type_id,
                    JSON_VALUE(value, '$.type.name') AS type,
                    CAST(JSON_VALUE(value, '$.possession') AS INT) AS possession,
                    CAST(JSON_VALUE(value, '$.possession_team.id') AS INT) AS possession_team_id,
                    JSON_VALUE(value, '$.possession_team.name') AS possession_team,
                    CAST(JSON_VALUE(value, '$.play_pattern.id') AS INT) AS play_pattern_id,
                    JSON_VALUE(value, '$.play_pattern.name') AS play_pattern,
                    value AS json_
                FROM 
                    OPENJSON((SELECT json_ FROM events WHERE match_id = ?));
                """

                # Extract the necessary data from the event
                params = (
                    match_id, # match_id
                    match_id  # match_id
                )

                # Execute the SQL query with parameters
                cursor.execute(sql, params)

                # Commit the changes
                conn.commit()

                print(f"Events ({i}/{len(files)}). Inserted data for match_id {match_id} into [events] and [events_details] tables.")

    # Close the connection
    cursor.close()
    conn.close()


def create_tables_sqlite(source, source_file):

    # Connect to the database
    conn = get_connection_pyodbc(source)
    cursor = conn.cursor()

    with open(source_file, 'r') as f:
        sql = f.read()
        cursor.executescript(sql)

    conn.commit()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        print(f"tabla creada: {table[0]}")

    cursor.close()
    conn.close()


def load_matches_data_into_database_from_folder (source, folder_name):
    """
    Connects to a database and imports match data from JSON files into specified database tables.
    This function processes match files, extracting detailed match information, including team, player, and game event details,
    and performs SQL insert operations to store this data in the database. It is designed to handle batch processing of multiple files
    and includes an interactive mode for user control over the execution process.

    Parameters:
    - source (str): The source of the database. Either "azure-sql", "azure-postgres", or "sqlite-local".
    - folder_name (str): The directory path where the match JSON files are stored.

    Functionality:
    - Database Connection: Establishes a connection to the SQL Server database using provided credentials.
    - File Processing: Iterates over JSON files in the specified directory, processing each file that ends with `.json`.
    - Data Extraction and Insertion:
      - For each match file, extracts comprehensive match data including teams, players, scores, and other relevant metadata.
      - Constructs and executes SQL queries to insert this data into the 'matches' table.
      - Handles additional details such as manager, stadium, and referee information for comprehensive match records.
    - User Interaction: Optionally prompts the user for confirmation before processing files if the `interactive` parameter is set to True.
    - Commit and Close: Commits the transactions to the database and closes the connection after all files are processed or upon user cancellation.

    Output:
    - Console Output: Provides feedback on the number of files processed and details about the data inserted, including match IDs and key event information.
    - Database Update: Updates the 'matches' table in the database with new data from the processed JSON files.
    """

    # Connect to the database
    conn = get_connection_pyodbc(source)
    cursor = conn.cursor()

    # Path to the match files
    matchesPath = os.path.join(folder_name, 'matches')
    total_files = 0

    # Count the total number of JSON files
    for dir in os.listdir(matchesPath):
        dir_path = os.path.join(matchesPath, dir)
        
        # Check if it is a directory
        if os.path.isdir(dir_path):
            # Iterate over each file in the directory
            for file in os.listdir(dir_path):
                if file.endswith(".json"):
                    total_files += 1  # Increment the counter for each JSON file

    print(f"Processing {total_files} [Matches] files...")
    print("---------------------------------------------")

    i=0
    j=0

    for dir in os.listdir(matchesPath):

        dir_path = os.path.join(matchesPath, dir)
        competition_id = dir_path.split('\\')[-1]
        
        # Check if it is a directory
        if os.path.isdir(dir_path):
            # Iterate over each file in the directory
            for file in os.listdir(dir_path):

                if file.endswith(".json"):

                    i+=1

                    file_path = os.path.join(dir_path, file)
                    season_id = file.replace('.json', '')

                    # check if the season_id, and the competition_id already exists in the matches table
                    sql = f"SELECT COUNT(*) FROM matches WHERE season_id = '{season_id}' AND competition_id = '{competition_id}'"
                    cursor.execute(sql)
                    count = cursor.fetchone()[0]

                    # if it already exists, skip the file
                    if count > 0:
                        print(f"There is already matches data for competition_id [{competition_id}], season_id [{season_id}] in the matches table. Skipping file...")
                        continue

                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        season_data = json.load(f)

                    j=0
                    for data in season_data:
                        j += 1
                        # Insert match data

                        def get_manager_info(managers):
                            if managers and isinstance(managers, list) and len(managers) > 0:
                                manager_name = managers[0].get('name', '').replace("'", "''")
                                manager_country = managers[0].get('country', {}).get('name', '').replace("'", "''")
                                return manager_name, manager_country
                            return None, None  # Return None if there are no managers or the structure is not as expected.

                        # Use the get_manager_info function for home and away teams.
                        home_manager_name, home_manager_country = get_manager_info(data['home_team'].get('managers'))
                        away_manager_name, away_manager_country = get_manager_info(data['away_team'].get('managers'))

                        # Stadium and referee, check if they exist before trying to access their properties.
                        stadium_id = data.get('stadium', {}).get('id')
                        stadium_name = data.get('stadium', {}).get('name', '').replace("'", "''")
                        stadium_country = data.get('stadium', {}).get('country', {}).get('name', '').replace("'", "''")

                        referee_id = data.get('referee', {}).get('id')
                        referee_name = data.get('referee', {}).get('name', '').replace("'", "''")
                        referee_country = data.get('referee', {}).get('country', {}).get('name', '').replace("'", "''")

                        sql = """
                            INSERT INTO matches (
                                match_id, match_date, competition_id, competition_name, competition_country,
                                season_id, season_name, 
                                home_team_id, home_team_name, home_team_gender, home_team_country, home_team_manager, home_team_manager_country,
                                away_team_id, away_team_name, away_team_gender, away_team_country, away_team_manager, away_team_manager_country,
                                home_score, away_score, result, match_week,
                                stadium_id, stadium_name, stadium_country, 
                                referee_id, referee_name, referee_country,
                                json_
                            )
                            VALUES (?, ?, ?, ?, ?, 
                            ?, ?, 
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?,
                            ?, ?, ?,
                            ?)
                        """
                        params = (
                            data['match_id'],
                            data['match_date'],
                            competition_id,
                            data['competition']['competition_name'].replace("'", "''"),
                            data['competition']['country_name'].replace("'", "''"),
                            season_id,
                            data['season']['season_name'].replace("'", "''"),
                            data['home_team']['home_team_id'],
                            data['home_team']['home_team_name'].replace("'", "''"),
                            data['home_team']['home_team_gender'].replace("'", "''"),
                            data['home_team']['country']['name'].replace("'", "''"),
                            home_manager_name,
                            home_manager_country,
                            data['away_team']['away_team_id'],
                            data['away_team']['away_team_name'].replace("'", "''"),
                            data['away_team']['away_team_gender'].replace("'", "''"),
                            data['away_team']['country']['name'].replace("'", "''"),
                            away_manager_name,
                            away_manager_country,
                            data['home_score'],
                            data['away_score'],
                            f"{data['home_score']} - {data['away_score']}",
                            data['match_week'],
                            stadium_id,
                            stadium_name,
                            stadium_country,
                            referee_id,
                            referee_name,
                            referee_country,
                            json.dumps(data).replace("'", "''")
                        )

                        # Execute the query with the given parameters
                        cursor.execute(sql, params)
                        conn.commit()
                        
                        home = data['home_team']['home_team_name'].replace("'", "''")
                        away = data['away_team']['away_team_name'].replace("'", "''")

                        print(f"Matches ({i}-{j}/{total_files}: {file}): Inserted data - match_id:{data['match_id']}, {data['match_date']}, {home}-{away}")

    cursor.close()
    conn.close()
    print(f"Process completed. {i} files processed.")


def get_json_events_details_from_match_id (source, match_id):
    """Retrieves events data from a database based on the given parameters.
    Parameters:
    - source (str): The source of the database. Either "azure-sql", "azure-postgres", or "sqlite-local".
    - match_id (str): The ID of the match to retrieve events for.
    Returns:
    - df (pandas.DataFrame): A DataFrame containing the events data.
    """

    conn = get_connection(source)

    query = f"""
            select json_
            from events_details
            where match_id = '{match_id}'
            order by period, timestamp;
            """    
    df = pd.read_sql(query, conn)
    return df


def download_match_yaml(source, table_name, match_id, column_name, local_folder, minutes_per_file):
    try:
        # Crear carpeta local recursivamente si no existe
        os.makedirs(local_folder, exist_ok=True)

        # Obtener conexión y cursor
        conn = get_connection_pyodbc(source)
        cursor = conn.cursor()

        # Definir la consulta
        query = f"""
            SELECT period, minute, {column_name} 
            FROM {table_name}
            WHERE match_id = {match_id} 
            ORDER BY period, minute
        """
        cursor.execute(query)

        # Inicializar variables para las salidas
        summary_output = ""
        summary_output_all = ""
        from_minute = -1
        last_minute = -1

        for row in cursor.fetchall():

            period = row[0]
            minute = row[1]
            summary = row[2]
            if from_minute == -1:
                from_minute = minute
            
            if minute > last_minute and last_minute != -1:

                s = source.replace("-", "_")
                filename = f"{s}_{table_name}_{column_name}_match_id_{match_id}_p_{str(period).zfill(2)}_m_{str(from_minute).zfill(3)}_m_{str(last_minute).zfill(3)}.yaml"
                summary_output = "events:" + summary_output 
                save_file(local_folder, filename, summary_output)
                summary_output = "" 
                from_minute =-1
                last_minute = -1

            # Reemplazar saltos de línea en summary para adaptarse al formato YAML
            formatted_summary = summary.replace('\n\n', '\n      ')

            # Crear formato estilo YAML para cada registro
            record = (
                f"\n  - table_name: {table_name}\n"
                f"    match_id: {match_id}\n"
                f"    period: {period}\n"
                f"    minute: {minute}\n"
                f"    description: |\n"
                f"      {formatted_summary}\n"
            )

            # Concatenar el encabezado y el resumen en estilo YAML
            summary_output += record
            summary_output_all += record

            if minute % minutes_per_file == 0 and minute != 0:
                last_minute = minute

        # Si queda contenido en summary_output, guardarlo en un archivo
        if summary_output:
            s = source.replace("-", "_")
            filename = f"{s}_{table_name}_{column_name}_match_id_{match_id}_p_{str(period).zfill(2)}_m_{str(from_minute).zfill(3)}_m_{str(minute).zfill(3)}.yaml"
            save_file(local_folder, filename, summary_output)

        # Guardar el archivo con todo el resumen
        if summary_output_all:
            s = source.replace("-", "_")
            filename = f"{s}_{table_name}_{column_name}_match_id_{match_id}__all_m_000_m_{str(minute).zfill(3)}.yaml"
            summary_output_all = "events:" + summary_output_all 
            save_file(local_folder, filename, summary_output_all)

    except Exception as e:
        handle_exception(e)


def save_file(folder_path, filename, content):
    """
    Guarda el contenido en el archivo especificado en la carpeta indicada.
    """
    try:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as e:
        raise RuntimeError(f"Error saving file {filename}.") from e


def handle_exception(e):
    """
    Maneja las excepciones de manera uniforme, extrayendo el traceback y lanzando una excepción más detallada.
    """
    tb = traceback.extract_tb(e.__traceback__)
    frame = tb[0]
    method_name = frame.name
    line_number = frame.lineno
    file_name = os.path.basename(frame.filename)
    raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error occurred.") from e


def get_games_with_embeddings(source, as_data_frame=False):
    """
    Retrieves the games that have embeddings.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
        match_id (int): The ID of the match.
    Returns:
        str: The game result data as a string.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        details_table = "events_details__15secs_agg"

        if source == "sqlite-local":
            details_table = "events_details__15secs_agg"
        if source == "azure-sql":
            details_table = "events_details__15secs_agg"
        if source == "azure-postgres":
            details_table = "events_details__quarter_minute"

        query = f"""
            SELECT m.match_id, m.home_team_name, m.away_team_name, m.home_score, m.away_score
            FROM matches m where m.competition_name = 'UEFA Euro' and m.season_name = '2024'
            AND (
                    (home_team_name = 'Spain' or away_team_name = 'Spain') or
                    (home_team_name = 'Spain' and away_team_name = 'England') or

                    (home_team_name = 'Spain' and away_team_name = 'Germany') or
                    (home_team_name = 'Netherlands' and away_team_name = 'England') or

                    (home_team_name = 'Spain' and away_team_name = 'France') or
                    (home_team_name = 'Netherlands' and away_team_name = 'Turkey') or
                    (home_team_name = 'Portugal' and away_team_name = 'France') or
                    (home_team_name = 'England' and away_team_name = 'Switzerland')
                )
            AND exists (select * from {details_table} where match_id = m.match_id and not summary is null)
            order by m.match_id desc
        """

#####       exists (select * from events_details__15secs_agg ed where ed.match_id = m.match_id and embedding_ada_002 is not null)
        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_game_result_data(source, match_id, as_data_frame=False):
    """
    Retrieves the game result data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
        match_id (int): The ID of the match.
    Returns:
        str: The game result data as a string.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT m.match_date, m.competition_name, m.season_name, m.home_team_name, m.away_team_name, m.result
            FROM matches m
            WHERE match_id = {match_id}
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_game_players_data(source, match_id, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
        match_id (int): The ID of the match.
    Returns:
        str: The player data as a string.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT team_name, player_name, from_time, to_time, position_name 
            FROM players
            WHERE match_id = {match_id}
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_database_schema(source, as_data_frame=False):
    """
    Retrieves the database schema.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The schema as a string.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        if source == "azure-sql" or source == "azure-postgres":

            query = f"""
                SELECT 
                    t.TABLE_NAME AS table_name,
                    STRING_AGG('| ' + c.COLUMN_NAME + ' ' + c.DATA_TYPE + ' |', ', ') AS columns_with_types
                FROM 
                    INFORMATION_SCHEMA.TABLES t
                JOIN 
                    INFORMATION_SCHEMA.COLUMNS c
                ON 
                    t.TABLE_NAME = c.TABLE_NAME
                -- WHERE 
                --    t.TABLE_TYPE = 'BASE TABLE'  -- Opcional: Filtrar solo tablas, no vistas
                GROUP BY 
                    t.TABLE_NAME
                ORDER BY 
                    t.TABLE_NAME;
            """

        elif source =="sqlite-local":

            query = f"""
                SELECT sql FROM sqlite_master WHERE type='table';
            """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_dynamic_sql(source, sql_query, as_data_frame=False):
    """
    Retrieves the database schema.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
        sql_query (str): The SQL query to execute.
        as_data_frame (bool): If True, the result is returned as a pandas DataFrame.
    Returns:
        str: The result as a string.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        df = pd.read_sql(sql_query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        raise e
    #     # raise exception
    #     tb = traceback.extract_tb(e.__traceback__)
    #     frame = tb[0]
    #     method_name = frame.name
    #     line_number = frame.lineno
    #     file_name = os.path.basename(frame.filename)
    #     raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_players_summary_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The player data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT competition_name, season_name, competition_country, player_name, team_name, position_name, count(DISTINCT m.match_id) count_matches
            FROM players p
            JOIN matches m ON p.match_id = m.match_id
            GROUP BY competition_name, season_name, competition_country, player_name, team_name, position_name
            ORDER BY competition_name, season_name, competition_country, player_name, team_name, position_name;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_teams_summary_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The player data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT team_name, sum(matches_count) as matches_count
            FROM (
                SELECT home_team_name team_name, count(DISTINCT match_id) as matches_count
                FROM matches
                GROUP BY home_team_name
                UNION 
                SELECT away_team_name team_name, count(DISTINCT match_id) as matches_count
                FROM matches
                GROUP BY away_team_name
                ) v
            GROUP BY team_name;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_events_summary_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The player data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = ""
        if source == "azure-postgres":
            query = f"""
                SELECT competition_name, season_name, play_pattern, possession_team, count(*) count_events
                FROM (select * from events_details limit 250000) as ed 
                JOIN matches m 
                ON ed.match_id = m.match_id
                GROUP BY competition_name, season_name, play_pattern, possession_team
                ORDER BY competition_name, season_name, play_pattern, possession_team;
            """

        if  source == "sqlite-local":
            # events_details table does not exist in sqlite-local
            query = f"""
                SELECT competition_name, season_name, '' play_pattern, '' possession_team, count(*) count_events
                FROM matches m 
                GROUP BY competition_name, season_name, play_pattern, possession_team
                ORDER BY competition_name, season_name, play_pattern, possession_team;
            """
            
        if source == "azure-sql":
            query = f"""
                SELECT competition_name, season_name, play_pattern, possession_team, count(*) count_events
                FROM (select top 250000 * from events_details) as ed 
                JOIN matches m 
                ON ed.match_id = m.match_id
                GROUP BY competition_name, season_name, play_pattern, possession_team
                ORDER BY competition_name, season_name, play_pattern, possession_team;
            """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_competitions_summary_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT competition_name, count(*) matches_count
            FROM matches
            GROUP BY competition_name
            ORDER BY competition_name;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_competitions_summary_with_teams_and_season_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT competition_name, season_name, team_name, sum(matches_count) as matches_count
            FROM (
                SELECT competition_name, home_team_name team_name, season_name, count(DISTINCT match_id) as matches_count
                FROM matches
                GROUP BY competition_name, season_name, home_team_name
                UNION 
                SELECT competition_name, away_team_name team_name, season_name, count(DISTINCT match_id) as matches_count
                FROM matches
                GROUP BY competition_name, season_name, away_team_name
                ) v
            GROUP BY competition_name, season_name, team_name;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e
    

def get_competitions_summary_with_teams_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT competition_name, team_name, sum(matches_count) as matches_count
            FROM (
                SELECT competition_name, home_team_name team_name, count(DISTINCT match_id) as matches_count
                FROM matches
                GROUP BY competition_name, home_team_name
                UNION 
                SELECT competition_name, away_team_name team_name, count(DISTINCT match_id) as matches_count
                FROM matches
                GROUP BY competition_name, away_team_name
                ) v
            GROUP BY competition_name, team_name;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_competitions_results_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT competition_name, result
                FROM matches;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e


def get_all_matches_data(source, as_data_frame=False):
    """
    Retrieves game matches data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query = f"""
            SELECT competition_name, competition_country, season_name, match_date, home_team_name team_name, 
                    result, home_score goals_scored, away_score goals_conceded
            FROM matches
            UNION ALL 
            SELECT competition_name, competition_country, season_name, match_date, away_team_name team_name, 
                    result, away_score goals_scored, home_score goals_conceded
            FROM matches
            order by competition_name, competition_country, season_name, match_date;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}] Error connecting or executing the query in the database.") from e


def get_tables_info_data(source, as_data_frame=False):
    """
    Retrieves tables data from the database.
    Args:
        source (str): The source of the database. Either "azure-sql", or "azure-postgres" or "sqlite-local".
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)

        query=""

        if source == "azure-sql":

            query = f"""
                SELECT 
                    s.name AS schema_name,
                    t.name AS table_name,
                    CAST(CAST(SUM(a.total_pages) * 8 / 1024.0 AS DECIMAL(10,2)) AS DECIMAL(10,0)) AS total_size_MB
                FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                JOIN sys.indexes i ON t.object_id = i.object_id
                JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                JOIN sys.allocation_units a ON p.partition_id = a.container_id
                GROUP BY 
                    s.name, t.name
                ORDER BY 
                    total_size_MB DESC;
            """

        if source == "azure-postgres":
    
            query = f"""
            SELECT
                pg_namespace.nspname AS schema_name,
                pg_class.relname AS table_name,
                pg_size_pretty(pg_total_relation_size(pg_class.oid)) AS total_size,
                pg_size_pretty(pg_relation_size(pg_class.oid)) AS table_size
            FROM
                pg_class
            JOIN
                pg_namespace ON pg_class.relnamespace = pg_namespace.oid
            WHERE
                pg_class.relkind = 'r'
            ORDER BY
                pg_total_relation_size(pg_class.oid) DESC;
        """

        df = pd.read_sql(query, conn)

        if as_data_frame:
            return df
        else:
            result = df.to_string(index=False)
            return result

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}] Error connecting or executing the query in the database.") from e

