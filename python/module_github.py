import os
import requests
import pandas as pd
import psycopg2
from psycopg2 import sql

def get_json_list(repo_owner, repo_name, dataset):
    """
    Retrieves a list of JSON files from a GitHub repository.
    It traverses the first level subdirs in the repository to find JSON files and their URLs.
    It does not handle nested subdirectories. It does not handle pagination.
    Args:
        repo_owner (str): The owner of the GitHub repository.
        repo_name (str): The name of the GitHub repository.
        dataset (str): The name of the dataset directory.
    Returns:
        pandas.DataFrame: A DataFrame containing the dataset, subdir, and URL of each JSON file.
    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs during the request.
        requests.exceptions.ConnectionError: If a connection error occurs during the request.
        requests.exceptions.Timeout: If a timeout error occurs during the request.
        requests.exceptions.RequestException: If a general request exception occurs.
        ValueError: If a value error occurs during the processing of files.
        Exception: If an unexpected error occurs.
    """
    
    # Base GitHub API URL
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/data/{dataset}"
    json_files = []

    try:

        response = requests.get(api_url)
        if response.status_code == 200:
            files = response.json()
            subdirs = [file['name'] for file in files if file['type'] == 'dir']

            # for each subdir, get the list of files
            for subdir in subdirs:

                subdir_url = f"{api_url}/{subdir}"
                subdir_response = requests.get(subdir_url)
                if subdir_response.status_code == 200:
                    subdir_files = subdir_response.json()
                    json_files += [[dataset, subdir, file['download_url']] for file in subdir_files if file['name'].endswith('.json')]
                else:
                    print(f"Error retrieving files in subdirectory: {subdir_response.status_code, subdir_response.text}")

    except (requests.exceptions.HTTPError, 
            requests.exceptions.ConnectionError, 
            requests.exceptions.Timeout, 
            requests.exceptions.RequestException) as req_err:
        print(f"Request Error: {req_err}")
    except ValueError as val_err:
        print(f"Value Error: {val_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Convert list of files to DataFrame
    df = pd.DataFrame(json_files, columns=["dataset", "subdir", "url"])
    return df

def download_file(url, path, dir, subdir):
    """
    Downloads a file from a URL and saves it in the destination directory.
    Args:
        url (str): The URL of the file to download.
        path (str): The path of the destination directory.
        dir (str): The name of the directory within the destination directory.
        subdir (str): The name of the subdirectory within the directory.
    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs during the request.
        requests.exceptions.ConnectionError: If there is a connection error.
        requests.exceptions.Timeout: If the request times out.
        requests.exceptions.RequestException: If an error occurs during the request.
        Exception: If an unexpected error occurs.
    Returns:
        None: Does not return any value. Prints messages to the console indicating the result of the download.
    """
    # Check if the path exists
    if not os.path.exists(path):
        print(f"The path '{path}' does not exist. Aborting.")
        return

    # Create the directory and subdirectory if they don't exist
    destination_directory = os.path.join(path, dir, subdir)
    os.makedirs(destination_directory, exist_ok=True)

    try:

        # get the filename from the url
        filename = url.split("/")[-1]

        # if the file already exists, skip the download
        if os.path.exists(os.path.join(destination_directory, filename)):
            print(f"File already exists at {destination_directory}. Skipping download.")
            return

        # Make a GET request to the file
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP error status codes

        # Extract the filename from the URL
        filename = os.path.basename(url)

        # Build the full path to save the file
        file_path = os.path.join(destination_directory, filename)

        # Save the file in the destination directory
        with open(file_path, 'wb') as file:
            file.write(response.content)

        print(f"File downloaded successfully at {file_path}")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
    except requests.exceptions.ConnectionError:
        print("Connection Error. Please check your internet connection.")
    except requests.exceptions.Timeout:
        print("The request has timed out.")
    except requests.exceptions.RequestException as err:
        print(f"Error making the request: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_github_data(repo_owner, repo_name, dataset, local_folder):
    """
    Retrieves data from a GitHub repository for the specified dataset and saves them to the specified directory.
    It respect the structure of the repository, and download the files in the subdirectories.
    For example, data in the repository is stored in the following structure:
    - data
        - matches
            - 1
                - 1.json
                - 2.json
            - 2
                - 221.json
                - 112.json
    
    Parameters:
    - repo_owner (str): The owner of the GitHub repository.
    - repo_name (str): The name of the GitHub repository.
    - dataset (str): The dataset to get the data.
    - local_folder (str): The local directory to save the downloaded files.
    Returns:
    None
    """

    # Get the list of JSON files for the dataset
    json_urls = get_json_list(repo_owner, repo_name, dataset)

    # Save the list of the Json_urls to a CSV file, and print the path where the Csv file is stored
    json_urls.to_csv(f"{local_folder}/{dataset}_urls.csv", index=False)
    print(f"File {dataset}_urls.csv saved in {local_folder}")

    # Assign the result of group by dataset, counting the number of records per dataset, to variable c
    c = json_urls.groupby(['dataset']).size().reset_index(name='counts')
    print(c)

    for _, row in json_urls.iterrows():
        dataset = row['dataset']
        subdir = row['subdir']
        file_url = row['url']
        print(f"dataset: {dataset}, subdir: {subdir}, url: {file_url}", end=" ")

        download_file(file_url, local_folder, dataset, subdir)

def  get_github_data_from_matches(repo_owner, repo_name, dataset, local_folder, server, database, username, password):

    try:        
        # Connect to the database
        conn = psycopg2.connect(
            host=server,
            database=database,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()

        count_query = sql.SQL(f"""select distinct match_id from matches order by match_id""")

        cursor.execute(count_query)

        # Store the number of records in variable c
        number_of_rows = cursor.rowcount
        i=1

        # For each match_id, download the data for the specified dataset
        for match_id in cursor.fetchall():
            match_id = match_id[0]

            # examples:
            # https://raw.githubusercontent.com/statsbomb/open-data/master/data/lineups/3943043.json
            # https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/3943043.json

            file_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/master/data/{dataset}/{match_id}.json"
            print(f"[{i}/{number_of_rows}] Source:{file_url}.", end=" ")

            download_file(file_url, local_folder, dataset, "")
            i+=1

    except Exception as e:
        print(f"Error connecting or executing the query in the database: {e}")

    finally:
        # Close the cursor and the connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()