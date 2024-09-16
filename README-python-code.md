# Project Documentation

## Introduction

This project contains three key Python modules: `module_azureopenai.py`, `module_github.py`, and `module_postgres.py`. Each module serves a specific purpose in managing data integrations across Azure OpenAI, GitHub repositories, and PostgreSQL databases. The primary functions of these modules include:

- **module_azureopenai.py**: Responsible for connecting to both local and Azure-hosted PostgreSQL databases. It includes methods for handling natural language tasks using OpenAI's Azure services, such as generating chat completions.
  
- **module_github.py**: Focused on interacting with GitHub repositories to retrieve and handle JSON datasets. This module connects to both local and Azure databases, allowing easy management and retrieval of repository contents.
  
- **module_postgres.py**: Designed for PostgreSQL data operations, this module manages data extraction and manipulation from both local and cloud-based databases. It handles specific data like football match details and results, enabling easy transfer between PostgreSQL databases.

Each of these modules is designed to work cohesively, ensuring seamless interaction with cloud and database services, while managing large datasets efficiently. This makes the system robust and scalable for various data operations in sports analytics.

## Modules Overview

| **Module Name**        | **Method Name**                                        | **Description**                                                                 |
|------------------------|--------------------------------------------------------|---------------------------------------------------------------------------------|
| module_azureopenai.py   | `get_connection`                                      | Establishes a connection to a PostgreSQL database (local or Azure).              |
| module_azureopenai.py   | `get_chat_completion_from_azure_open_ai`               | Generates a chat completion from Azure OpenAI using input messages.              |
| module_azureopenai.py   | `count_tokens`                                        | Counts the number of tokens in a given text.                                     |
| module_azureopenai.py   | `get_tokens_statistics_from_table_column`              | Gets token statistics from a specified table column.                             |
| module_azureopenai.py   | `create_and_download_detailed_match_summary`           | Creates and downloads a detailed match summary.                                  |
| module_azureopenai.py   | `create_events_summary_per_pk_from_json_rows_in_database` | Creates an events summary from JSON rows in a database.                          |
| module_azureopenai.py   | `create_match_summary`                                | Creates a match summary for a given match.                                       |
| module_azureopenai.py   | `search_details_using_embeddings`                     | Searches for details using embeddings.                                           |
| module_azureopenai.py   | `get_dataframe_from_ids`                              | Retrieves a DataFrame based on IDs.                                              |
| module_azureopenai.py   | `process_prompt`                                      | Processes a prompt for use in OpenAI.                                            |
| module_azureopenai.py   | `export_script_result_to_text`                        | Exports the result of a script to a text file.                                   |
| module_github.py        | `get_connection`                                      | Establishes a connection to a PostgreSQL database (local or Azure).              |
| module_github.py        | `get_json_list_from_repo`                             | Retrieves a list of JSON files from a GitHub repository.                         |
| module_github.py        | `download_file_from_repo_url`                         | Downloads a file from a GitHub repository using its URL.                         |
| module_github.py        | `download_data_from_github_repo`                      | Downloads data from a GitHub repository.                                         |
| module_github.py        | `get_github_data_from_matches`                        | Retrieves GitHub data for specified matches.                                     |
| module_postgres.py      | `get_connection`                                      | Establishes a connection to a PostgreSQL database (local or Azure).              |
| module_postgres.py      | `copy_data_from_postgres_to_azure`                    | Copies data from a local PostgreSQL database to an Azure-hosted database.        |
| module_postgres.py      | `load_lineups_data_into_postgres`                     | Loads lineups data into the PostgreSQL database.                                 |
| module_postgres.py      | `insert_players`                                      | Inserts player data into the PostgreSQL database.                                |
| module_postgres.py      | `load_events_data_into_postgres`                      | Loads events data into the PostgreSQL database.                                  |
| module_postgres.py      | `load_matches_data_into_postgres_from_folder`          | Loads match data from a folder into the PostgreSQL database.                     |
| module_postgres.py      | `get_manager_info`                                    | Retrieves manager information for a given match.                                 |
| module_postgres.py      | `get_json_events_details_from_match_id`               | Retrieves event details in JSON format for a specific match ID.                  |
| module_postgres.py      | `download_match_script`                               | Downloads the match script for a specified match.                                |
| module_postgres.py      | `get_game_result_data`                                | Retrieves game result data for a specific match ID.                              |
| module_postgres.py      | `get_game_players_data`                               | Fetches player data for a specific match.                                        |
| module_postgres.py      | `get_players_summary_data`                            | Retrieves summary data for players in a given match.                             |
| module_postgres.py      | `get_teams_summary_data`                              | Retrieves summary data for teams in a given match.                               |
| module_postgres.py      | `get_events_summary_data`                             | Retrieves summary data for events in a given match.                              |
| module_postgres.py      | `get_competitions_summary_data`                       | Retrieves summary data for competitions.                                         |
| module_postgres.py      | `get_competitions_summary_with_teams_and_season_data` | Retrieves summary data for competitions with team and season details.            |
| module_postgres.py      | `get_competitions_summary_with_teams_data`            | Retrieves competition summary data with team details.                            |
| module_postgres.py      | `get_competitions_results_data`                       | Retrieves results data for competitions.                                         |
| module_postgres.py      | `get_all_matches_data`                                | Retrieves data for all matches.                                                  |
| module_postgres.py      | `get_tables_info_data`                                | Retrieves metadata information for PostgreSQL tables.                            |

