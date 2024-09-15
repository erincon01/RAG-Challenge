import os
"""
This script loads events and lineups data into a PostgreSQL database from a local folder.
Parameters:
- repo_owner (str): The owner of the repository where the data is stored.
- repo_name (str): The name of the repository where the data is stored.
- local_folder (str): The path to the local folder containing the data.
Steps:
1. Load events data into the PostgreSQL database.
2. Load lineups data into the PostgreSQL database.
3. Load events_details table using the script /postgres/tables_setup_load_events_details_from_postgres.sql.
Note: The matches data is not necessary to load again as it was already loaded in step 01.
Usage:
- Set the environment variables REPO_OWNER, REPO_NAME, and LOCAL_FOLDER to the appropriate values.
- Run the script.
"""
from module_postgres import load_matches_data_into_postgres_from_folder, load_events_data_into_postgres, load_lineups_data_into_postgres

if __name__ == "__main__":

    # statsbomb data parameters
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')
    local_folder = os.getenv('LOCAL_FOLDER')

    # 1) matches data is not necesary because it was loaded in step 01
    # load_matches_data_into_postgres_from_folder(local_folder)

    # 2) load events data into postgres
    load_events_data_into_postgres(local_folder)

    # 3) load lineups data into postgres
    load_lineups_data_into_postgres(local_folder)

    # 4) # events_details table
    # this table is loaded using the script /postgres/tables_setup_load_events_details_from_postgres.sql
    # reason is because it is more efficient to build the data using json functions in postgres vs trasnferring the data row by row
    
