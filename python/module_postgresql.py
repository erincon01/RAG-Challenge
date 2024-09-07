import os
import json
import psycopg2
from psycopg2 import sql

def copy_data_from_local_to_azure(server, database, username, password, server_azure, database_azure, username_azure, password_azure, table_name, columns_list):
    """
    Connects to a local PostgreSQL database and copies data from specified tables to an Azure PostgreSQL database.
    This function facilitates the migration of data between two PostgreSQL databases, allowing for seamless transfer
    of information from a local environment to a cloud-based service such as Azure.

    Parameters:
    - server (str): The hostname or IP address of the local PostgreSQL server.
    - database (str): The name of the local PostgreSQL database to connect to.
    - username (str): The username used to authenticate with the local database.
    - password (str): The password used to authenticate with the local database.
    - server_azure (str): The hostname or IP address of the Azure PostgreSQL server.
    - database_azure (str): The name of the Azure PostgreSQL database to connect to.
    - username_azure (str): The username used to authenticate with the Azure database.
    - password_azure (str): The password used to authenticate with the Azure database.
    - table_name (str): The name of the table to copy data from the local database to the Azure database.
    - column_list (str): A list of column names to copy from the local table to the Azure table.

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
        # Connect to the local database
        conn = psycopg2.connect(
            host=server,
            database=database,
            user=username,
            password=password
        )
        cursor = conn.cursor()

        # Connect to the Azure database
        conn_azure = psycopg2.connect(
            host=server_azure,
            database=database_azure,
            user=username_azure,
            password=password_azure
        )
        cursor_azure = conn_azure.cursor()

        # Query to select all data from the table
        select_query = sql.SQL(f"""SELECT {columns_list} FROM {table_name};""")
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
        print(f"Error copying data to Azure database: {e}")

    finally:
    
        # Close the cursor and the connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

        if cursor_azure:
            cursor_azure.close()
        if conn_azure:
            conn_azure.close()

        
def load_lineups_data(server, database, username, password, local_folder):
    """
    Connects to a PostgreSQL database and imports lineup data from JSON files into specified database tables.
    Processes each JSON file, extracting relevant team and player information, and performs SQL insert operations
    to store this data in the database. Designed to handle batch processing of multiple files and provides options
    for interactive user control over the execution.

    Parameters:
    - server (str): The hostname or IP address of the PostgreSQL server.
    - database (str): The name of the PostgreSQL database to connect to.
    - username (str): The username used to authenticate with the database.
    - password (str): The password used to authenticate with the database.
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
    conn = psycopg2.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    
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


def load_events_data(server, database, username, password, local_folder):
    """
    Connects to a PostgreSQL database and imports event data from JSON files into specified database tables.
    This function processes event files, extracting detailed event information, and performs SQL insert operations
    to store this data in the database. It is capable of handling batch processing of multiple files and includes
    an interactive mode for user control over the execution process.

    Parameters:
    - server (str): The hostname or IP address of the PostgreSQL server.
    - database (str): The name of the PostgreSQL database to connect to.
    - username (str): The username used to authenticate with the database.
    - password (str): The password used to authenticate with the database.
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
    conn = psycopg2.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    
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



def load_matches_data_into_db(local_folder, server, database, username, password):
    """
    Connects to a PostgreSQL database and imports match data from JSON files into specified database tables.
    This function processes match files, extracting detailed match information, including team, player, and game event details,
    and performs SQL insert operations to store this data in the database. It is designed to handle batch processing of multiple files
    and includes an interactive mode for user control over the execution process.

    Parameters:
    - local_folder (str): The directory path where the match JSON files are stored.
    - server (str): The hostname or IP address of the PostgreSQL server.
    - database (str): The name of the PostgreSQL database to connect to.
    - username (str): The username used to authenticate with the database.
    - password (str): The password used to authenticate with the database.

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
    conn = psycopg2.connect(
        host=server,
        database=database,
        user=username,
        password=password
    )
    
    cursor = conn.cursor()

    # Path to the match files
    matchesPath = os.path.join(local_folder, 'matches')
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


def update_embeddings(server, database, username, password, model, tablename, batch_size, num_rows=-1):
    """
    Connects to a PostgreSQL database and updates embeddings in a specified table using external AI models.
    This function interfaces with AI services such as Azure's OpenAI or local AI models to generate text embeddings
    for data entries that lack embeddings. It is capable of batch processing entries and provides detailed logging
    of the update process.

    Parameters:
    - server (str): The hostname or IP address of the PostgreSQL server.
    - database (str): The name of the PostgreSQL database to connect to.
    - username (str): The username used to authenticate with the database.
    - password (str): The password used to authenticate with the database.
    - model (str): The model identifier to specify which embedding service to use ('azure_open_ai' or 'azure_local_ai').
    - tablename (str): The name of the database table where embeddings need to be updated.
    - batch_size (int): Number of rows to process in each batch.
    - num_rows (int, optional): Total number of rows to update; defaults to -1, indicating all eligible rows should be processed.

    Functionality:
    - Database Connection: Establishes a connection to the PostgreSQL database using provided credentials.
    - Model Selection: Based on the 'model' parameter, selects the appropriate AI model for generating embeddings.
    - Row Processing: Iteratively updates rows in the specified table that are missing embeddings, using the selected AI model to generate and store embeddings.
    - Transaction Management: Commits changes to the database in batches, ensuring data integrity and allowing for recovery in case of errors.
    - Logging: Provides continuous feedback on the number of rows processed and remaining, and detailed error messages in case of failures.

    Output:
    - Console Output: Provides ongoing feedback during the process, including progress indicators and summaries once the process is completed.
    - Database Update: Directly updates the 'embeddings' field in the specified table for rows that were missing embeddings.
    """


    # if model is azure_open_ai, use the create_embeddings function from azure_openai
    # if model is azure_local_ai, use the create_embeddings function from azure_local_ai

    function_name = ""
    model_name = ""
    if model == "azure_open_ai":
        function_name = "azure_openai.create_embeddings"
        model_name = "text-embedding-ada-002"
        
    elif model == "azure_local_ai":
        function_name = "azure_local_ai.create_embeddings"  # Change to the correct function name
        model_name = "multilingual-e5-small:v1"  # Change to the correct model name

    else:
        print(f"Unsupported model: {model}")
        return

    try:        
        # Connect to the database
        conn = psycopg2.connect(
            host=server,
            database=database,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()

        # print server and database
        
        # count the rows that do not have embeddings and print it on the screen
        count_query = sql.SQL(f"""
            SELECT COUNT(*) FROM {tablename}
            WHERE embeddings IS NULL AND json_ IS NOT NULL
        """)
        cursor.execute(count_query)
        count = cursor.fetchone()[0]
        print(f"Total rows in table [{tablename}] to process: {count}. Batch size {batch_size}.", end="")

        # Query to update the rows
        update_query = sql.SQL(f"""
            UPDATE {tablename}
            SET embeddings = {function_name}('{model_name}', json_)
            WHERE id IN (
                SELECT id FROM {tablename} 
                WHERE embeddings IS NULL AND 
                json_ IS NOT NULL
                LIMIT {batch_size}
            )
        """)

        processed_rows = 0

        while True:
            cursor.execute(update_query)
            conn.commit()
            rows_affected = cursor.rowcount
            processed_rows += rows_affected

            # Break the loop if no rows were affected (when there are no more rows matching the condition)
            if rows_affected == 0:
                break

            # print dot without line break
            print(".", end="")

            # Print every 10 iterations if num_rows is different from -1
            if (processed_rows % 100 == 0):
                print()
                print(f"Processed {processed_rows} rows.", end="")
            
            # Break the loop if we reach the specified number of rows to update
            if num_rows != -1 and processed_rows >= num_rows:
                break

        print(f"Total rows processed: {processed_rows}.")

    except Exception as e:
        print(f"Error connecting or executing the query in the database: {e}")

    finally:
        # Close the cursor and the connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
