
import os
"""
Downloads matches data from a GitHub repository and stores it into a local folder.
Then, loads the matches data into a PostgreSQL database.
Finally, retrieves lineups and events data from the GitHub repository based on the matches stored in the database.
Parameters:
- repo_owner (str): The owner of the GitHub repository.
- repo_name (str): The name of the GitHub repository.
- local_folder (str): The path to the local folder where the data will be downloaded and stored.
Returns:
None
"""
from module_github import download_data_from_github_repo, get_github_data_from_matches
from module_postgres import load_matches_data_into_postgres_from_folder

if __name__ == "__main__":

    # statsbomb data parameters
    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')
    local_folder = os.getenv('LOCAL_FOLDER')
    
    # 1) download all matches data from GitHub repository (statsbomb) to local folder
    download_data_from_github_repo(repo_owner, repo_name, "matches", local_folder)

    # 2) store into the postgres database the matches data
    load_matches_data_into_postgres_from_folder(local_folder)

    # 3) get lineups and events data, based on the matches stored in the database. 
    #    this method only downloads the data from the repository into the local folder.
    #    it does not store the data into the database.
    get_github_data_from_matches(repo_owner, repo_name, "lineups", local_folder)
    get_github_data_from_matches(repo_owner, repo_name, "events", local_folder)

