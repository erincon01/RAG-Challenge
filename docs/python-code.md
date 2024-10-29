# Project Documentation

## Introduction

This project is built around three core Python modules: `module_azureopenai.py`, `module_github.py`, and `module_data.py`. These modules provide essential functionalities to handle data interactions and natural language processing, making it easier to manage large datasets and integrate various cloud services, including Azure and GitHub.

The **`module_azureopenai.py`** focuses on leveraging OpenAI’s capabilities within Azure to handle natural language tasks. It facilitates connecting to both local and cloud-hosted PostgreSQL databases and performing operations like generating chat completions, counting tokens, and processing text data. This module is pivotal for any tasks involving AI-driven language models integrated into data pipelines.

The **`module_github.py`** is designed for seamless integration with GitHub repositories, allowing users to interact with JSON datasets hosted on GitHub. It automates the process of connecting to repositories, retrieving data, and downloading files, making it easy to manage datasets that are version-controlled or shared within GitHub environments. This module is ideal for those looking to automate their interactions with GitHub-hosted data.

The **`module_data.py`** serves as the backbone for all PostgreSQL and SQL Server data operations. It simplifies the extraction, loading, and manipulation of data in both local and Azure PostgreSQL and SQL Server databases. This module is especially useful for managing structured data like football match details, enabling efficient storage, retrieval, and analysis of large datasets.

Together, these modules create a robust system capable of handling complex data workflows. They streamline the interaction with cloud services, facilitate the management of datasets, and integrate natural language processing tasks, making the project well-suited for data-intensive applications like sports analytics.


## Modules Overview: `module_github.py`

### Introduction

The `module_github.py` module is designed to facilitate seamless interaction with GitHub repositories. It provides methods for connecting to GitHub, retrieving JSON datasets, and downloading files, making it an essential tool for managing version-controlled data and automating repository interactions. This module is particularly useful when working with data stored on GitHub and integrating it with PostgreSQL databases.

### High-Level Overview

This module simplifies the process of interacting with GitHub repositories, automating tasks such as retrieving a list of files, downloading files, and fetching specific data. By streamlining these interactions, the `module_github.py` helps to automate data ingestion workflows, particularly for large datasets that are maintained or versioned on GitHub. It is capable of establishing connections to both local and cloud-hosted PostgreSQL databases, allowing for efficient data management.

Whether you need to download datasets for analysis or automate the process of keeping your local database updated with the latest repository data, this module provides the necessary tools to handle these tasks efficiently. By focusing on JSON file handling and repository data management, it ensures a smooth integration between GitHub and PostgreSQL databases.

### Functions Overview

| **Function Name**                                      | **Description**                                                                 |
|--------------------------------------------------------|---------------------------------------------------------------------------------|
| `get_connection`                                       | Establishes a connection to a PostgreSQL database, either local or Azure-hosted. |
| `get_json_list_from_repo`                              | Retrieves a list of JSON files from a specified GitHub repository.               |
| `download_file_from_repo_url`                          | Downloads a specific file from a GitHub repository using its URL.                |
| `download_data_from_github_repo`                       | Automates the process of downloading data from a GitHub repository.              |
| `get_github_data_from_matches`                         | Retrieves data for specific matches from a GitHub repository, typically JSON.    |




## Modules Overview: `module_azureopenai.py`

### Introduction

The `module_azure_openai.py` is a key component of the project that integrates with Azure OpenAI services to manage natural language tasks. It provides methods that enable the interaction between PostgreSQL databases and Azure-hosted AI models, making it possible to generate chat completions, count tokens, and retrieve token statistics from tables. This module is designed for efficient handling of natural language processing tasks and database operations, particularly when working with large datasets in cloud environments.

### High-Level Overview

This module plays a crucial role in streamlining tasks that require interaction with AI models for generating text-based responses or performing token-based operations. It simplifies the connection to both local and cloud-hosted PostgreSQL databases, ensuring that data operations can be performed seamlessly while utilizing the power of OpenAI services hosted in Azure. The main functionalities of the module include generating chat completions from prompts, counting tokens in text, and performing analytical operations on database tables, such as retrieving token statistics.

The module is structured to provide a robust set of tools for users who need to integrate AI-driven tasks into their data pipelines. Whether it's generating summaries from large datasets or analyzing token usage, the `module_azure_openai.py` ensures that complex tasks can be performed with minimal effort.

### Functions Overview

| **Function Name**                                      | **Description**                                                                 |
|--------------------------------------------------------|---------------------------------------------------------------------------------|
| `get_connection`                                       | Establishes a connection to a PostgreSQL database, either local or Azure-hosted. |
| `get_chat_completion_from_azure_open_ai`               | Generates a chat completion using OpenAI's Azure services from a given input.    |
| `count_tokens`                                         | Counts the number of tokens present in a given text or prompt.                   |
| `get_tokens_statistics_from_table_column`              | Retrieves token statistics (mean, median, etc.) from a specific table column.    |
| `create_and_download_detailed_match_summary`           | Generates and downloads a detailed summary for a football match.                 |
| `create_events_summary_per_pk_from_json_rows_in_database` | Creates a summary of events based on JSON data rows from a database.             |
| `create_match_summary`                                 | Creates a match summary for a given match using AI-generated content.            |
| `search_details_using_embeddings`                      | Performs a search for detailed information using text embeddings.                |
| `get_dataframe_from_ids`                               | Retrieves a pandas DataFrame based on specified IDs.                             |
| `process_prompt`                                       | Processes an input prompt to prepare it for use with OpenAI services.            |
| `export_script_result_to_text`                         | Exports the results of a script execution to a text file.                        |




## Modules Overview: `module_data.py`

### Introduction

The `module_data.py` module is designed to manage comprehensive data operations across both SQL Server and PostgreSQL databases. It includes a wide range of functions for extracting, loading, and manipulating structured datasets, such as football match details, player data, event summaries, and competition results. This module is highly flexible and robust, supporting both local and cloud-hosted databases, making it ideal for applications that handle large datasets and require efficient data processing workflows.

### High-Level Overview

This module provides a set of tools for seamless interaction with SQL Server and PostgreSQL databases. Whether the goal is to bulk load data into tables, extract detailed match and player information, or retrieve event and competition summaries, `module_data.py` offers the necessary functions. It simplifies the process of transferring data between local and cloud environments and ensures that both SQL Server and PostgreSQL instances can be managed with minimal effort.

Supporting large-scale datasets, the module includes methods for loading data from various sources (e.g., folders containing match data) and retrieving key insights such as player statistics and competition results. Its flexibility in handling both SQL Server and PostgreSQL allows it to be used in a variety of data integration scenarios, ensuring that the user can work across different database platforms effortlessly.

### Functions Overview

| **Function Name**                                      | **Description**                                                                 |
|--------------------------------------------------------|---------------------------------------------------------------------------------|
| `get_connection`                                       | Establishes a connection to either SQL Server or PostgreSQL (local or cloud-hosted). |
| `load_lineups_data_into_database`                      | Loads lineups data into a specified SQL Server or PostgreSQL table.              |
| `load_matches_data_into_database_from_folder`          | Bulk loads match data from a folder into SQL Server or PostgreSQL databases.     |
| `insert_players`                                       | Inserts player data into SQL Server or PostgreSQL.                              |
| `load_events_data_into_database`                       | Loads event data into SQL Server or PostgreSQL databases.                       |
| `load_competitions_data`                               | Loads competition data into SQL Server or PostgreSQL.                           |
| `get_game_players_data`                                | Retrieves detailed player data for a specific match from SQL Server or PostgreSQL. |
| `get_events_summary_data`                              | Fetches summary data for events in a given match from SQL Server or PostgreSQL.  |
| `get_competitions_summary_data`                        | Retrieves summary data for all competitions from SQL Server or PostgreSQL.       |
| `get_game_result_data`                                 | Retrieves match result data for a specific match from SQL Server or PostgreSQL.  |
| `get_competitions_results_data`                        | Fetches results data for competitions across multiple seasons.                  |
| `get_game_lineup_data`                                 | Retrieves the lineup data for a specific match from SQL Server or PostgreSQL.    |
| `get_match_statistics`                                 | Fetches detailed statistics for a specific match from SQL Server or PostgreSQL.  |
| `get_tables_info_data`                                 | Retrieves metadata and table information from SQL Server or PostgreSQL databases. |
| `copy_data_from_postgres_to_sql_server`                | Copies data from a PostgreSQL database to a SQL Server database.                 |

