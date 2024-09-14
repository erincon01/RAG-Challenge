import os
import json
import psycopg2
import traceback
from datetime import datetime
from psycopg2 import sql
import pandas as pd
from module_azureopenai import get_chat_completion_from_azure_open_ai

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
        # Connect to the other database configuration
        conn = psycopg2.connect(
            host=os.getenv('DB_SERVER'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

    return conn

def copy_data_from_postgres_to_azure(table_name, columns_list, filter_predicate="", match_id=-1):
    """
    Connects to a local PostgreSQL database and copies data from specified tables to an Azure PostgreSQL database.
    This function facilitates the migration of data between two PostgreSQL databases, allowing for seamless transfer
    of information from a local environment to a cloud-based service such as Azure.

    Parameters:
    - table_name (str): The name of the table to copy data from the local database to the Azure database.
    - column_list (str): A list of column names to copy from the local table to the Azure table.
    - filter_predicate (str): A filter predicate to apply when selecting data from the local table.
    - match_id (int): The ID of the match to copy data for. If <= 0, all data from the table will be copied.

    Functionality:
    - Database Connection: Establishes connections to the local and Azure PostgreSQL databases using provided credentials.
    - Data Transfer: Copies data from specified tables in the local database to corresponding tables in the Azure database.
    - Transaction Management: Ensures data integrity by committing changes to the Azure database after successful data transfer.
    - Error Handling: Provides detailed error messages in case of connection issues or data transfer failures.

    Output:
    - Console Output: Provides feedback on the data transfer process, including the number of rows copied and any errors encountered.
    - Database Update: Updates the specified tables in the Azure PostgreSQL database with data from the local database.
    """

    try:
        conn = get_connection("local")
        cursor = conn.cursor()

        conn_azure = get_connection("azure")
        cursor_azure = conn_azure.cursor()

        select_query=""
        # if match_id <= 0, then copy all data from the table
        if filter_predicate:
            # Query to select all data from the table
            select_query = sql.SQL(f"""SELECT {columns_list} FROM {table_name} WHERE {filter_predicate};""")
        else:
            if match_id <= 0:
                # Query to select all data from the table
                select_query = sql.SQL(f"""SELECT {columns_list} FROM {table_name};""")
            else:
                # Query to select all data from the table
                select_query = sql.SQL(f"""SELECT {columns_list} FROM {table_name} WHERE match_id = {match_id};""")

        cursor.execute(select_query)

        # Fetch all rows from the local database
        rows = cursor.fetchall()
        num_rows = len(rows)

        # Insert each row into the Azure database
        i = 0
        for row in rows:

            insert_query = sql.SQL(f"""
                INSERT INTO {table_name} ({columns_list})
                VALUES ({', '.join(['%s' for _ in range(len(row))])})
            """)

            # Execute the INSERT query
            cursor_azure.execute(insert_query, row)
            conn_azure.commit()

            i += 1
            # pitnar cadad 10 filas procesadas
            if i % 10 == 0:
                print(f"{i} of {num_rows} rows copied from [{table_name}] table to Azure database.")

    except Exception as e:
        # raise exception
        tb = traceback.extract_tb(e.__traceback__)
        frame = tb[0]
        method_name = frame.name
        line_number = frame.lineno
        file_name = os.path.basename(frame.filename)
        raise RuntimeError(f"[{file_name}].[{method_name}].[line-{line_number}] Error connecting or executing the query in the database.") from e

        
def load_lineups_data_into_postgres(local_folder):
    """
    Connects to a PostgreSQL database and imports lineup data from JSON files into specified database tables.
    Processes each JSON file, extracting relevant team and player information, and performs SQL insert operations
    to store this data in the database. Designed to handle batch processing of multiple files and provides options
    for interactive user control over the execution.

    Parameters:
    - local_folder (str): The directory path where the lineup JSON files are stored.

    Functionality:
    - Database Connection: Establishes a connection to the PostgreSQL database using provided credentials.
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
    conn = get_connection("local")
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
                    print(f"The match_id [{match_id}] already exists in the lineups table. Skipping file...")
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
                    VALUES (%s, %s, %s, %s, %s, %s)
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

                print(f"Lineups ({i}/{len(files)}). Inserted data for match_id {match_id} into [lineups] table: home:{data[0]['team_name']}, away:{data[1]['team_name']}.")

    # Close the connection
    cursor.close()
    conn.close()


def load_events_data_into_postgres(local_folder):
    """
    Connects to a PostgreSQL database and imports event data from JSON files into specified database tables.
    This function processes event files, extracting detailed event information, and performs SQL insert operations
    to store this data in the database. It is capable of handling batch processing of multiple files and includes
    an interactive mode for user control over the execution process.

    Parameters:
    - local_folder (str): The directory path where the event JSON files are stored.

    Functionality:
    - Database Connection: Establishes a connection to the PostgreSQL database using provided credentials.
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
    conn = get_connection("local")
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
                    print(f"The match_id [{match_id}] already exists in the events table. Skipping file...")
                    continue

                with open(os.path.join(eventsPath, file), 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)

                sql = """
                    INSERT INTO events (
                        match_id, json_
                    )
                    VALUES (%s, %s)
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
                    index,
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
                    %s AS match_id,
                    data->>'id' AS id_guid,
                    (data->>'index')::INT AS index,
                    (data->>'period')::INT AS period,
                    data->>'timestamp' AS timestamp,
                    (data->>'minute')::INT AS minute,
                    (data->>'second')::INT AS second,
                    (data->'type'->>'id')::INT AS type_id,
                    data->'type'->>'name' AS type,
                    (data->>'possession')::INT AS possession,
                    (data->'possession_team'->>'id')::INT AS possession_team_id,
                    data->'possession_team'->>'name' AS possession_team,
                    (data->'play_pattern'->>'id')::INT AS play_pattern_id,
                    data->'play_pattern'->>'name' AS play_pattern,
                    data AS json_
                FROM events,
                    jsonb_array_elements((json_)::jsonb) AS elem(data)
                WHERE match_id = %s;  """

                # Extract the necessary data from the event
                params = (
                    match_id,  # match_id
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



def load_matches_data_into_postgres_from_folder (folder_name):
    """
    Connects to a PostgreSQL database and imports match data from JSON files into specified database tables.
    This function processes match files, extracting detailed match information, including team, player, and game event details,
    and performs SQL insert operations to store this data in the database. It is designed to handle batch processing of multiple files
    and includes an interactive mode for user control over the execution process.

    Parameters:
    - folder_name (str): The directory path where the match JSON files are stored.

    Functionality:
    - Database Connection: Establishes a connection to the PostgreSQL database using provided credentials.
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
    conn = get_connection("local")
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

        competition_id = dir_path.split('/')[-1]
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
                            VALUES (%s, %s, %s, %s, %s, 
                            %s, %s, 
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s)
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


def get_json_events_details_from_match_id (match_id):
    """Retrieves events data from a database based on the given parameters.
    Parameters:
    - match_id (str): The ID of the match to retrieve events for.
    Returns:
    - df (pandas.DataFrame): A DataFrame containing the events data.
    """

    conn = get_connection("local")
    cursor = conn.cursor()

    sql = f"""
            select json_
            from events_details
            where match_id = '{match_id}'
            order by period, timestamp;
            """    
    cursor.execute(sql)

    # Convert the result to a dataframe
    df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

    return df

def download_match_script(source, table_name, match_id, column_name, local_folder, minutes_chunks):

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT period, minute, {column_name} 
            FROM {table_name}
            WHERE match_id = {match_id} 
            ORDER BY period, minute
        """)
        cursor.execute(query)
        summary_output = ""
        summary_output_all = ""

        for row in cursor.fetchall():

            period = row[0]
            minute = row[1]
            summary = row[2]
            # pintar en pantalla el periodo y el minuto
            header = "\n" + f"--------------------------------------------" + "\n"
            header += f"Table_name: {table_name}, match_id: {match_id}, period: {str(period).zfill(2)}, minute: {str(minute).zfill(3)}" + "\n"
            header += f"--------------------------------------------" + "\n"
            summary_output += header + summary
            summary_output_all += header + summary

            # si i > 0 y i > minute_chunks, entonces se crea un nuevo archivo, sino, se añade a summary
            if minute > 0 and minute % minutes_chunks == 0:
                filename = f"{table_name}_{column_name}_minutes_{match_id}-{str(period).zfill(2)}-{str(minute).zfill(3)}.txt"
                with open(os.path.join(local_folder, filename), "w", encoding="utf-8") as f:
                    f.write(summary_output)
                summary_output = ""

        # si summary_output no está vacío, se crea un archivo con el contenido restante
        if summary_output:
            filename = f"{table_name}_{column_name}_minutes_{match_id}-{str(period).zfill(2)}-{str(minute).zfill(3)}.txt"
            with open(os.path.join(local_folder, filename), "w", encoding="utf-8") as f:
                f.write(summary_output)

        if summary_output_all:
            filename = f"{table_name}_{column_name}_{match_id}___all.txt"
            with open(os.path.join(local_folder, filename), "w", encoding="utf-8") as f:
                f.write(summary_output_all)

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
        source (str): The source of the database (either "azure" or any other value).
        match_id (int): The ID of the match.
    Returns:
        str: The game result data as a string.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT m.match_date, m.competition_name, m.season_name, m.home_team_name, m.away_team_name, m.result
            FROM matches m
            WHERE match_id = {match_id}
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "No results found."

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

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
        source (str): The source of the database (either "azure" or any other value).
        match_id (int): The ID of the match.
    Returns:
        str: The player data as a string.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT team_name, player_name, from_time, to_time, position_name 
            FROM players
            WHERE match_id = {match_id}
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "No results found."

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

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

def get_players_summary_data(source, as_data_frame=False):
    """
    Retrieves game player data from the database.
    Args:
        source (str): The source of the database (either "azure" or any other value).
    Returns:
        str: The player data as a string.
        data_frame: The player data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT player_name, team_name, position_name, count(DISTINCT match_id) count_matches
            FROM players
            GROUP BY player_name, team_name, position_name
            ORDER BY player_name, team_name, position_name;
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "No results found."

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

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
        source (str): The source of the database (either "azure" or any other value).
    Returns:
        str: The player data as a string.
        data_frame: The player data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT team_name, sum(num_matches) as num_matches
            FROM (
                SELECT home_team_name team_name, season_name, count(DISTINCT match_id) as num_matches
                FROM matches
                GROUP BY home_team_name, season_name
                UNION 
                SELECT away_team_name team_name, season_name, count(DISTINCT match_id) as num_matches
                FROM matches
                GROUP BY away_team_name, season_name
                ) v
            GROUP BY team_name;
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "No results found."

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

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
        source (str): The source of the database (either "azure" or any other value).
    Returns:
        str: The player data as a string.
        data_frame: The player data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT competition_name, count(*) count_events
            FROM events_details ed 
            JOIN matches m 
            ON ed.match_id = m.match_id
            GROUP BY competition_name
            ORDER BY competition_name;
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "No results found."

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

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
        source (str): The source of the database (either "azure" or any other value).
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        cursor = conn.cursor()


        query = sql.SQL(f"""
            SELECT competition_name, count(*) matches_count
            FROM matches
            GROUP BY competition_name
            ORDER BY competition_name;
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "No results found."

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

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

def get_matches_summary_data(source, as_data_frame=False):
    """
    Retrieves game matches data from the database.
    Args:
        source (str): The source of the database (either "azure" or any other value).
    Returns:
        str: The player data as a string.
        data_frame: The competition data as a pandas DataFrame.
    Raises:
        Exception: If there is an error connecting to or executing the query in the database.
    """

    try:

        conn = get_connection(source)
        cursor = conn.cursor()

        query = sql.SQL(f"""
            SELECT competition_name, season_name, match_date, home_team_name, away_team_name, result
            FROM matches
            order by 1, 2, 3;
        """)

        cursor.execute(query)
        rowCount = cursor.rowcount

        if rowCount == 0:
            return "No results found."

        # convertir el resultado a un pandas dataframe
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])

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
