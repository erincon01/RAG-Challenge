# RAG Challenge

## Environment setup

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Fill in the .env file with your data. see .env.example file.

```bash
# Hudl Statsbomb
BASE_URL=https://github.com/statsbomb/open-data/raw/master/data
REPO_OWNER=statsbomb
REPO_NAME=open-data
LOCAL_FOLDER=./data

# sql paas Azure
DB_SERVER_AZURE=server_name.database.windows.net
DB_NAME_AZURE=database_name
DB_USER_AZURE=user_name
DB_PASSWORD_AZURE=password

# postgres paas Azure
DB_SERVER_AZURE_POSTGRES=server_name.postgres.database.azure.com
DB_NAME_AZURE_POSTGRES=database_name
DB_USER_AZURE_POSTGRES=user_name
DB_PASSWORD_AZURE_POSTGRES=password

# Azure openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_KEY=your_key
OPENAI_ENDPOINT=https://your_endpoint.openai.azure.com/
```

## Data preparation

Data preparacion consists in downloading the data to local folder.
Then store the data into local postgres, and then load the data into Azure postgres.
If needed help on seting up progres in local and Azure read read the relevent products documentation. These are some usefull links:

- <https://learn.microsoft.com/en-us/azure/postgresql/single-server/quickstart-create-server-database-portal>
- <https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/>

### Download data from Hudl Statsbomb to local

This process download the data from Hudl Statsbomb to local.
The process is this:

- Download to local the data from all the `matches`.
- Stores into postgres the matches data.
- Based on the data stored into the dabase, then the `lineups`, and `events` data is downloaded.

**Note**: before step #2, you need to setup the postgres database locally, and create the relevant tables. Table script is located in the `postgres` folder, in the file `tables_setup_onprem.sql` [file path](./postgres/tables_setup_onprem.sql)

This process involves downloading data from a GitHub repository, storing it in a local folder, and optionally loading it into a PostgreSQL database for further analysis. The script `01-download_to_local.py` coordinates this process by utilizing methods from `module_github.py` and `module_postgres.py`.

#### Steps Involved

1. **Download Matches Data from GitHub Repository to Local Folder**  
   The method `download_data_from_github_repo` from `module_github.py` is used to download the data.

2. **Store Matches Data into PostgreSQL Database**  
   Once the matches data is downloaded to the local folder, it is inserted into the PostgreSQL database using `load_matches_data_into_postgres_from_folder` from `module_postgres.py`.

3. **Download Lineups and Events Data**  
   After storing the match data, lineups and events data is retrieved from the GitHub repository using `get_github_data_from_matches` from `module_github.py`.

#### Detailed Method Descriptions

##### `download_data_from_github_repo(repo_owner, repo_name, data_type, local_folder)`

- **Purpose:** Downloads data from a specific GitHub repository and stores it in a local folder.
- **Parameters:**
  - `repo_owner` (str): The owner of the repository (e.g., 'statsbomb').
  - `repo_name` (str): The name of the repository (e.g., 'open-data').
  - `data_type` (str): The type of data to download (e.g., 'matches', 'lineups', 'events').
  - `local_folder` (str): The local folder where the data will be saved.
- **Process:**
  1. Connects to the GitHub repository using the provided credentials.
  2. Downloads the specified data type.
  3. Stores the downloaded data in the provided local folder.

##### `load_matches_data_into_postgres_from_folder(local_folder)`

- **Purpose:** Loads the downloaded matches data from the local folder into a PostgreSQL database.
- **Parameters:**
  - `local_folder` (str): The path to the folder where the matches data is stored locally.
- **Process:**
  1. Connects to the PostgreSQL database.
  2. Reads the downloaded match files.
  3. Inserts the data into the appropriate database tables.

##### `get_github_data_from_matches(repo_owner, repo_name, data_type, local_folder)`

- **Purpose:** Downloads additional data (such as lineups or events) from the GitHub repository based on the matches stored in the PostgreSQL database.
- **Parameters:**
  - `repo_owner` (str): The owner of the repository.
  - `repo_name` (str): The name of the repository.
  - `data_type` (str): The type of data to download (e.g., 'lineups', 'events').
  - `local_folder` (str): The local folder where the downloaded data will be saved.
- **Process:**
  1. Connects to the GitHub repository.
  2. Downloads the required data based on the stored match data.
  3. Saves the data to the specified local folder.

### Loading Data into PostgreSQL from Local Folder

This script (`02-load_data_into_postgres_from_local.py`) is responsible for loading events and lineups data from a local folder into a PostgreSQL database. It assumes that the matches data was already loaded in a previous step, and focuses on events, lineups, and building the `events_details` table efficiently.

#### Process Overview

1. **Load Events Data into PostgreSQL:**  
   The method `load_events_data_into_postgres` is used to load the events data from the local folder into the PostgreSQL database.

2. **Load Lineups Data into PostgreSQL:**  
   The method `load_lineups_data_into_postgres` loads the lineups data from the local folder into the database.

3. **Load `events_details` Table Using SQL Script:**  
   The `events_details` table is built using a dedicated SQL script (`tables_setup_load_events_details_from_postgres.sql`). This step leverages PostgreSQL’s JSON functions for efficient data transformation directly within the database, avoiding row-by-row transfers.

#### Detailed Method Descriptions

##### `load_events_data_into_postgres(local_folder)`

- **Purpose:** Loads the events data from the local folder into the PostgreSQL database.
- **Parameters:**
  - `local_folder` (str): The path to the folder containing the downloaded events data.
- **Process:**
  1. Connects to the PostgreSQL database.
  2. Reads the events data from the local folder.
  3. Inserts the events data into the appropriate PostgreSQL table.

##### `load_lineups_data_into_postgres(local_folder)`

- **Purpose:** Loads the lineups data from the local folder into the PostgreSQL database.
- **Parameters:**
  - `local_folder` (str): The path to the folder containing the downloaded lineups data.
- **Process:**
  1. Connects to the PostgreSQL database.
  2. Reads the lineups data from the local folder.
  3. Inserts the lineups data into the appropriate PostgreSQL table.

##### Loading Data into `events_details` Table

For efficiency, as previous step loaded `events` data into the database, it is more efficient to INSERT FROM SELECT vs row by row INSERT.

This SQL script is designed to load event details from the `events` table into the `events_details` table in a PostgreSQL database. It processes each record in the `events` table, extracts relevant fields from a JSON structure, and inserts them into `events_details`.

1. **Cursor Declaration:**  
   A cursor (`cur`) is declared to fetch records from the `events` table.

2. **Loop to Process Records:**  
   The script loops through each record retrieved by the cursor and extracts the event details stored in a JSON field.

3. **Insertion into `events_details`:**  
   For each record, the following fields are inserted into `events_details`:
   - `match_id`
   - `id_guid` (extracted from the JSON field `data->>'id'`)
   - `index`, `period`, `timestamp`, `minute`, `second`
   - `type_id` and `type` (extracted from the JSON field `data->'type'`)
   - `possession`, `possession_team_id`, `possession_team`
   - `play_pattern_id` and `play_pattern`
   - The entire JSON object (`json_`)

4. **Logging the Process:**  
   After each insertion, a `RAISE NOTICE` statement is triggered, which prints the processed `match_id` and the total number of records inserted for that match.

### Load data from local Postgres to Azure Postgres PaaS Flexible

Before loading the data into Postgres PaaS Flexible, you need to setup the database in Azure.
Some tips:

- make sure your ISP don't block the port 5432, that is the default por for Postgres.
- you cannot change the default port in PaaS Postgres (not allowed in server configuration portal). TODO: test is from Azure Cli.
- add your public IP to the firewall rules in Postgres instance configuration.

In this project, we are using these extensions:

- vector
- azure_ai
- azure_local_ai

that requires this machine configuration:
"memory-optimized Azure VM SKUs with a minimum of 4 vCores. Today, if you are using a VM that does
not meet the minimum requirements, the azure_local_ai extension will not appear in the list of
available extensions in Server parameters"

Aditionally, the azure_local_ai, extension, as of today is only available in these regions:

- Australia East
- East USA
- France Central **
- Japan East
- UK South
- West Europe
- West USA
-

<https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/azure-local-ai>

these links have helped us to understand and install the requirements:

- <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/generative-ai-azure-overview>
- <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-extensions>
- <https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-extensions>

Note. In some cases, you might need to change the configuration parameters for the postgres inscance using azure cli:

<https://learn.microsoft.com/en-us/cli/azure/postgres/flexible-server?view=azure-cli-latest>

this will help you:

```bash

az postgres flexible-server parameter set `
    --resource-group <rg>  `
    --server-name <server> `
    --subscription <subs_id> `
    --name azure.extensions `
    --value vector,azure_ai,azure_local_ai


az postgres flexible-server update `
--name <dbname> `
--resource-group <rgname> `
--admin-password <password> `
```

After setting up the instance, you need to enable the extensions, and the endpoint to Azure AI. Use the following:

``` sql
-- azure_ai

CREATE EXTENSION azure_ai;
CREATE EXTENSION vector;

select azure_ai.set_setting('azure_openai.endpoint','https://<endpoint>.openai.azure.com'); 
select azure_ai.set_setting('azure_openai.subscription_key', 'key');

select azure_ai.get_setting('azure_openai.endpoint');
select azure_ai.get_setting('azure_openai.subscription_key');
select azure_ai.version();

ALTER EXTENSION azure_ai UPDATE;
ALTER EXTENSION vector UPDATE;


-- azure_local_ai

SELECT * FROM pg_available_extensions where name like '%vector%' or  name like '%azure%';

SHOW azure.extensions;

CREATE EXTENSION azure_local_ai;
CREATE EXTENSION vector;

SELECT azure_local_ai.get_setting('intra_op_parallelism');
SELECT azure_local_ai.get_setting('inter_op_parallelism');
SELECT azure_local_ai.get_setting('spin_control');

ALTER EXTENSION azure_local_ai UPDATE;
ALTER EXTENSION vector UPDATE;

```

If you need deep dive into the setup procedure, use the script setup_postgres-doc-resources.sql, located in the postges folder [filename](./postgres/setup_postgres-doc-resources.sql).

After configuring the server, run the script tables_setup_azure_local_ai.sql, in postgres folder, that create the relevent tables in postgres Azure [filename](./postgres/tables_setup_azure_local_ai.sql).

Now, you can run the phyton script: 03-load_tables_from_local_to_postgres_azure.py located in the python folder. [filename](./python/03-load_tables_from_local_to_postgres_azure.py).

## Start the application (streamlit)

```bash
python -m streamlit run app.py
streamlit hello
```

## Modules description

### 1. module_azureopenai.py

The `module_azureopenai.py` module integrates OpenAI's Azure services with PostgreSQL databases, allowing users to interact with both local and cloud-hosted databases. This module provides functionalities for natural language processing tasks, such as generating chat completions and processing prompts using Azure OpenAI. Additionally, it includes tools to manage data like match summaries and event details, offering seamless communication between PostgreSQL databases and Azure-based AI models, making it an essential component for advanced data analytics in sports or other domains.

### 2. module_github.py

The `module_github.py` module is designed to facilitate seamless interaction with GitHub repositories, particularly for retrieving and managing structured data such as JSON files. It allows users to download data directly from repositories, integrate this data with local or cloud-hosted PostgreSQL databases, and automate workflows that involve handling large datasets from GitHub. With functionality to fetch specific files or entire datasets, this module is key to efficiently managing GitHub-hosted data in environments that require regular updates from repositories.

### 3. module_postgres.py

The `module_postgres.py` module is built to manage data stored in PostgreSQL databases, both locally and in Azure-hosted environments. It provides a range of functionalities including establishing database connections, loading data such as match results and player details, and synchronizing data between local and cloud databases. This module also supports the extraction and manipulation of large datasets, enabling efficient data analysis and integration for sports analytics or any application that relies on PostgreSQL for storage and processing of complex data.

Full list of the methogs for each py file is in [README-python-code](./docs/python-code.md).

## Usage of vector databases in SQL PaaS

- feature: <https://github.com/Azure-Samples/azure-sql-db-vector-search>
- requirements: <https://github.com/Azure-Samples/azure-sql-db-vector-search?tab=readme-ov-file#prerequisites>
- Sign up: <https://aka.ms/azuresql-vector-eap>

## Data distribution

This script is in [tables_data_distribution](.\postgres\tables_data_distribution.sql)

### competitions by country/region

```sql
select competition_country, count(distinct season_name) seasons
from matches m
group by competition_country
order by seasons DESC limit 10;
```

![alt text](images/image.png)

### competitions count by country/region

```sql
select competition_country, count(distinct competition_name) competitions
from matches m
group by competition_country
order by competitions DESC limit 10;
```

![alt text](images/image-1.png)

### seasons by country/region

```sql
select distinct competition_country, season_name
from matches m
order by competition_country limit 10;
```

![alt text](images/image-2.png)

### seasons2 by country/region

```sql
select distinct competition_country, season_name
from matches m
order by season_name limit 10;
```

![alt text](images/image-3.png)

### recent season by country/region

```sql
select competition_country, competition_name, season_name, count(*) matches
group by competition_country, competition_name, season_name
order by season_name DESC limit 15;
```

![STI: alt text](images/image-4.png)
