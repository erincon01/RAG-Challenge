import os
import requests
import pandas as pd
import psycopg2
from psycopg2 import sql

def fetch_json_data(url):
    """
    Fetches JSON data from a given URL.
    Args:
        url (str): The URL to fetch JSON data from.
    Returns:
        dict: The JSON data retrieved from the URL.
    Raises:
        HTTPError: If the HTTP request returns a 4xx or 5xx status code.
    """
    response.raise_for_status()

    # Fetch JSON data from a URL
    response = requests.get(url)
    response.raise_for_status()  # Raise exception for 4xx/5xx HTTP status codes
    return response.json()


import requests
import pandas as pd

def get_json_list(repo_owner, repo_name, dataset):
    """
    Retrieves a list of JSON files from a GitHub repository.
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
    page = 1
    per_page = 1000  # GitHub API max per page

    try:
        while True:
            # Make the request to the API with pagination
            response = requests.get(api_url, params={'page': page, 'per_page': per_page})
            
            if response.status_code == 200:
                files = response.json()
                
                if not files:
                    break  # Exit loop if no more files
                
                # Extract JSON files from the current page
                json_files += [[dataset, "", file['download_url']] for file in files if file['name'].endswith('.json')]
                
                # Process subdirectories
                subdirs = [file['name'] for file in files if file['type'] == 'dir']
                
                for subdir in subdirs:
                    subdir_url = f"{api_url}/{subdir}"
                    subdir_page = 1
                    
                    while True:
                        subdir_response = requests.get(subdir_url, params={'page': subdir_page, 'per_page': per_page})
                        
                        if subdir_response.status_code == 200:
                            subdir_files = subdir_response.json()
                            
                            if not subdir_files:
                                break  # Exit loop if no more files in subdir
                            
                            # Add JSON files from subdirectories
                            json_files += [[dataset, subdir, file['download_url']] for file in subdir_files if file['name'].endswith('.json')]
                            subdir_page += 1
                        else:
                            print(f"Error retrieving files in subdirectory: {subdir_response.status_code, subdir_response.text}")
                            break
                
                page += 1
            else:
                print(f"Error retrieving files: {response.status_code, response.text}")
                break

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

def get_github_data(repo_owner, repo_name, datasets, dir_destino):
    """
    Retrieves data from a GitHub repository for the specified datasets and saves them to the specified directory.
    Parameters:
    - repo_owner (str): The owner of the GitHub repository.
    - repo_name (str): The name of the GitHub repository.
    - datasets (list): A list of datasets to retrieve from the repository.
    - dir_destino (str): The destination directory to save the downloaded files.
    Returns:
    None
    """


    # OLD PROCESS. NOT NECESARY FOR LINEUPS AND EVENTS.
    # STILL VALID FOR MATCHES

    # For each dataset
    for dataset in datasets:
        json_urls = get_json_list(repo_owner, repo_name, dataset)

        # guardar json_urls en un archivo csv
        json_urls.to_csv(f"{dir_destino}/{dataset}_urls.csv", index=False)

        # pintar la ruta del archivo csv
        print(f"File {dataset}_urls.csv saved in {dir_destino}")


        # Assign the result of group by dataset, counting the number of records per dataset, to variable c
        c = json_urls.groupby(['dataset']).size().reset_index(name='counts')
        print(c)

        for _, row in json_urls.iterrows():
            dataset = row['dataset']
            subdir = row['subdir']
            file_url = row['url']
            print(f"dataset: {dataset}, subdir: {subdir}, url: {file_url}")

            download_file(file_url, dir_destino, dataset, subdir)

def  get_github_data_from_matches(repo_owner, repo_name, dataset, dir_destino, server, database, username, password):

    try:        
        # Connect to the database
        conn = psycopg2.connect(
            host=server,
            database=database,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()

        count_query = sql.SQL(f"""select distinct match_id from matches where 
                              not exists (select * from {dataset} where {dataset}.match_id = matches.match_id)""")

        cursor.execute(count_query)

        # poner en variable c el número de registros
        number_of_rows = cursor.rowcount
        i=1

        # para cada match_id, descargar los datos de lineups y events
        for match_id in cursor.fetchall():
            match_id = match_id[0]

            # https://raw.githubusercontent.com/statsbomb/open-data/master/data/lineups/3888713.json

            file_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/master/data/{dataset}/{match_id}.json"
            download_file(file_url, dir_destino, dataset, "")

            # pintar la ruta del archivo csv
            print(f"[{i}/{number_of_rows}] File {match_id}.json saved in {dir_destino}/{dataset}")
            i+=1

    except Exception as e:
        print(f"Error connecting or executing the query in the database: {e}")

    finally:
        # Close the cursor and the connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()