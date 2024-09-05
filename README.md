# statsbomb-loader
statsbomb loader

- Load data from https://github.com/statsbomb/open-data into postgres.

- WIP for Microsoft RAG challenge:
https://github.com/microsoft/RAG_Hack?tab=readme-ov-file#raghack-lets-build-rag-applications-together

- Official event: https://reactor.microsoft.com/es-es/reactor/events/23332/


## Install dependencies:

Copy code
```bash
pip install -r requirements.txt
```

## Configure environment variables:

Fill in the .env file with your data.

```bash
    # Base URL to access data on GitHub
    BASE_URL=https://github.com/statsbomb/open-data/raw/master/data

    REPO_OWNER=statsbomb
    REPO_NAME=open-data
    DATASETS=events, lineups, matches, three-sixty
    DIR_DESTINATION=./data
    DIR_SOURCE=./data

    # Database configuration
    DB_SERVER=your_server_name.database.windows.net
    DB_NAME=your_database_name
    DB_USER=your_username
    DB_PASSWORD=your_password
```

Run the script:

```bash
python main.py
```


## Usage of vector databases in SQL PaaS:

- feature: https://github.com/Azure-Samples/azure-sql-db-vector-search
- requirements: https://github.com/Azure-Samples/azure-sql-db-vector-search?tab=readme-ov-file#prerequisites
- sign up: https://aka.ms/azuresql-vector-eap


## Use case

```bash
    +-----------------------------------------+
    |               User                      |
    |-----------------------------------------|
    | Asks a question to the OpenAI chatbot   |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           OpenAI Chatbot                |
    |-----------------------------------------|
    | 1. Receives the user's question         |
    | 2. Sends the query to the Plugin        |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           Search Plugin                 |
    |-----------------------------------------|
    | 1. Generates the query embedding using   |
    |    OpenAI                                |
    | 2. Performs a semantic search in the     |
    |    PostgreSQL database                  |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |       PostgreSQL with pgvector          |
    |-----------------------------------------|
    | 1. Stores player data with embeddings    |
    | 2. Performs search based on embedding    |
    |    similarity                            |
    | 3. Returns relevant results              |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           Search Plugin                 |
    |-----------------------------------------|
    | 1. Receives results from PostgreSQL     |
    | 2. Generates a summary or response using |
    |    OpenAI (if necessary)                 |
    +-------------------+---------------------+
                        |
                        v
    +-------------------+---------------------+
    |           OpenAI Chatbot                |
    |-----------------------------------------|
    | 1. Receives the response from the Plugin |
    | 2. Presents the response to the user     |
    +-----------------------------------------+

```


## Data distribution

this script is located in [tables_data_distribution](.\postgres\tables_data_distribution.sql)


### competitions by country/region
```bash
select competition_country, count(distinct season_name) seasons
from matches m
group by competition_country
order by seasons DESC limit 10;
```

![alt text](.\images\image.png)

### competitions by country/region
```bash
select competition_country, count(distinct competition_name) competitions
from matches m
group by competition_country
order by competitions DESC limit 10;
```
![alt text](.\images\image-1.png)

### seasons by country/region
```bash
select distinct competition_country, season_name
from matches m
order by competition_country limit 10;
```

![alt text](.\images\image-2.png)

### seasons by country/region
```bash
select distinct competition_country, season_name
from matches m
order by season_name limit 10;
```

![alt text](.\images\image-3.png)

### recent season by country/region
```bash
select competition_country, competition_name, season_name, count(*) matches
group by competition_country, competition_name, season_name
order by season_name DESC limit 15;
```

![alt text](.\images\image-4.png)

