import os
"""
Downloads matches data from a GitHub repository and stores it into a local folder.
Then, loads the matches data into a SQL PaaS database.
Finally, retrieves lineups and events data from the GitHub repository based on the matches stored in the database.
Parameters:
- repo_owner (str): The owner of the GitHub repository.
- repo_name (str): The name of the GitHub repository.
- local_folder (str): The path to the local folder where the data will be downloaded and stored.
Returns:
None
"""
from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_sql_azure import load_matches_data_into_database_from_folder, create_tables_sqlite

if __name__ == "__main__":

    # StatsBomb data parameters
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')
    local_folder = os.getenv('LOCAL_FOLDER')
    
    # 1) Download all matches data from the GitHub repository (StatsBomb) to the local folder
    # download_data_from_github_repo(repo_owner, repo_name, "matches", local_folder)

    # 2) Store the matches data into the Azure SQL database
    # load_matches_data_into_database_from_folder("azure-sql", local_folder)

    # 3) Get lineups and events data based on the matches stored in the database.
    #    This method only downloads the data from the repository into the local folder.
    #    It does not store the data into the database.
    # get_github_data_from_matches(repo_owner, repo_name, "lineups", local_folder)
    # get_github_data_from_matches(repo_owner, repo_name, "events", local_folder)
