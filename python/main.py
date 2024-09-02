import os
import json
import requests
import psycopg2
from psycopg2 import sql
import pandas as pd
from module_github import get_github_data
from module_postgresql import put_data_into_postgres

if __name__ == "__main__":

    # get data from github and store in local

    repo_owner = os.getenv('REPO_OWNER')
    repo_name = os.getenv('REPO_NAME')
    datasets = os.getenv('DATASETS').split(',')
    dir_destino = os.getenv('DIR_DESTINO')
    dir_source = os.getenv('DIR_FUENTE')
    
    # remove wait spaces
    datasets = [dataset.strip() for dataset in datasets]

    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    # bajar datos desde repositorio de github a directorio destino (dir_destino)
    # get_github_data (repo_owner, repo_name, datasets, dir_destino)

    dir_source = dir_destino

    # cargar datos en postgres desde directorio fuente (dir_source)
    put_data_into_postgres(server, database, username, password, dir_destino)


