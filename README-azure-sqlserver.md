# RAG Challenge

## Environment setup

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Fill in the .env file with your data. see .env.example file.

```bash
# statsbomb
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

## Data preparation Overview

This process involves setting up an Azure SQL PaaS environment, downloading data to a local environment, loading the data into the database, and creating stored procedures for generating summaries and embeddings using OpenAI APIs. The process covers granular event data aggregation at 15-second and minute levels and utilizes OpenAI's API to generate text summaries and embeddings. Additionally, the process includes optional rebuilding of embeddings for specific matches.

---

## Step-by-Step Documentation

### 00. Azure SQL PaaS Setup

**File:** `00_tables_setup_azure_sql_paas.sql`

This script sets up the necessary tables in an Azure SQL PaaS instance to store event data. It defines two key aggregation tables: 
- `events_details__15secs_agg`: Stores detailed event data aggregated every 15 seconds.
- `events_details__minute_agg`: Stores detailed event data aggregated by minute.

The script also creates indices for optimizing query performance and sets up the primary and foreign keys for efficient relational data handling.

---

### 01. Download Data to Local

**File:** `01_download_to_local.py`

This Python script downloads event data from a remote source (e.g., an API or external database) and saves it locally. The key steps in this script include:
- Authentication with the remote source.
- Fetching the required event data.
- Saving the data in a format suitable for loading into the local database.

---

### 02. Load Data into Database

**File:** `02_load_data_into_database_from_local.py`

This Python script loads the downloaded event data into the SQL tables that were set up in the previous step. It performs the following operations:
- Connects to the Azure SQL PaaS instance.
- Reads the locally stored event data files.
- Inserts the data into the corresponding SQL tables (`events_details__15secs_agg` and `events_details__minute_agg`).

---

### 03. Create Aggregation Tables

**File:** `03_table_event_details_15secs_agg.sql` and `03_table_event_details_minute_agg.sql`

These SQL scripts create the aggregation tables for storing event details. Specifically:
- **`03_table_event_details_15secs_agg.sql`**: Defines the structure of the `events_details__15secs_agg` table, aggregating data at 15-second intervals.
- **`03_table_event_details_minute_agg.sql`**: Defines the structure of the `events_details__minute_agg` table, aggregating data by minute.

Both tables store JSON event data and contain columns for storing embeddings that will be generated later using OpenAI's API.

---

### 04. Create OpenAI Stored Procedures

**File:** `04_create_openai_stored_procedures_api_key_needed.sql`

This script creates stored procedures that call the OpenAI API to generate text summaries and embeddings for the event data stored in the aggregation tables. The key procedures include:
- **`dbo.get_chat_completion`**: Generates a text summary from the JSON event data.
- **`dbo.get_embeddings`**: Generates embeddings for the text summary using different OpenAI models (`embedding_ada_002` and `embedding_3_small`).

These procedures are essential for processing the event data and adding useful insights.

---

### 05. Test OpenAI Stored Procedures

**File:** `05_test_openai_stored_procedure.sql`

This script provides test cases to validate the stored procedures created in the previous step. It includes:
- Calling the stored procedures with sample data.
- Verifying that the procedures correctly generate summaries and embeddings.
- Checking the output for errors or discrepancies.

---

### 06. Convert JSON to Summary

**File:** `06_openai_convert_json_to_summary.sql`

This stored procedure processes JSON event data and generates text summaries using the OpenAI API. The process involves:
- Iterating over records in the `events_details__minute_agg` table.
- For each record, generating a summary and embeddings, and updating the record with this information.
- The procedure can be executed for specific `match_id`s to limit the scope of the operation.

---

### 07. Rebuild Embeddings (Optional)

**File:** `07_openai_rebuild_embeddings_optional.sql`

This optional procedure allows for the regeneration of embeddings for specific matches. It sets the `embedding_ada_002` and `embedding_3_small` columns to `NULL` and then regenerates the embeddings using the OpenAI API. This procedure is useful when embeddings need to be updated or corrected for a particular match.

---
