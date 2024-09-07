"""
Main script for loading data from GitHub and storing it in a PostgreSQL database.
This script retrieves data from a GitHub repository and saves it locally. Then, it loads the data into a PostgreSQL database.

Environment variables:
- REPO_OWNER: The owner of the GitHub repository.
- REPO_NAME: The name of the GitHub repository.
- DATASETS: Comma-separated list of datasets to download from the repository.
- local_folder: The destination directory to save the downloaded datasets.
- DIR_FUENTE: The source directory containing the downloaded datasets.
- DB_SERVER: The server address of the PostgreSQL database.
- DB_NAME: The name of the PostgreSQL database.
- DB_USER: The username for accessing the PostgreSQL database.
- DB_PASSWORD: The password for accessing the PostgreSQL database.

Functions:
- put_data_into_postgres: Loads data from the source directory into the PostgreSQL database.
- update_embeddings: Updates embeddings in the specified table using the specified model.

Usage:
1. Set the required environment variables.
2. Run the script.
Note: The script assumes that the necessary modules 'module_github' and 'module_postgresql' are available.
"""

import os
from module_github import get_github_data, get_github_data_from_matches
from module_postgresql import load_matches_data_into_db, load_lineups_data, load_events_data, update_embeddings

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

    # 1) download all matches data from GitHub repository (statsbomb) to local folder
    # get_github_data(repo_owner, repo_name, "matches", local_folder)

    # 2) store into the database the matches data
    # load_matches_data_into_db(local_folder, server, database, username, password)

    # 3) get lineups and events data, based on the matches stored in the database. 
    #    this method only downloads the data from the repository into the local folder.
    #    it does not store the data into the database.
    # get_github_data_from_matches(repo_owner, repo_name, "lineups", local_folder, server, database, username, password)
    # get_github_data_from_matches(repo_owner, repo_name, "events", local_folder, server, database, username, password)


    # 4) load downloadded data into PostgreSQL from local folder
    load_lineups_data(server, database, username, password, local_folder)
    load_events_data(server, database, username, password, local_folder)

    # For azure_open_ai or azure_local_ai
    model = "azure_local_ai"  # azure_open_ai,
    # azure_local_ai (see azure_open_ai documentation, only supported in specific regions and Memory Optimized, E4ds_v5, 4 vCores, 32 GiB RAM, 128 GiB storage)

    # Update embeddings for different tables
    # update_embeddings(server, database, username, password, model, "events", 10, -1)
    # update_embeddings(server, database, username, password, model, "lineups", 10, -1)
    # update_embeddings(server, database, username, password, model, "events_details", 10, -1)
    # update_embeddings(server, database, username, password, model, "matches", 10, -1)

