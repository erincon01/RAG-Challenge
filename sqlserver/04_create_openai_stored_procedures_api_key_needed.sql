/*

    This script performs the following tasks:

    1. Creates database credentials to store the API key for Azure OpenAI service.
       - Checks if a master key exists and creates one if it doesn't.
       - Drops and recreates a database scoped credential with the provided API key.

    2. Creates stored procedures for interacting with the Azure OpenAI API:
       - [dbo].[get_embeddings]: Fetches embeddings for a given text using specified models.
       - [dbo].[get_chat_completion]: Generates chat completions based on system messages and user prompts.

    3. Creates stored procedures to add summaries and embeddings to event details:
       - dbo.add_summary_to_json_in_events_details__minute_agg: Adds summaries and embeddings to the `events_details__minute_agg` table.
       - dbo.add_summary_to_json_in_events_details__15secs_agg: Adds summaries and embeddings to the `events_details__15secs_agg` table.

    4. Creates a stored procedure to rebuild embeddings in the `events_details__15secs_agg` table:
       - dbo.rebuild_embeddings_in_events_details__15secs_agg: Recalculates embeddings for existing summaries in the `events_details__15secs_agg` table.
*/

/*

SUPPORTED EMBEDDING MODELS DUE TO SIZE LIMITATIONS

Model	Max Input Size	Vector Size
text-embedding-ada-002	8,192 tokens	1,536 dimensions
text-embedding-3-small	8,191 tokens	1,536 dimensions

OPENAI_MODEL=gpt-4o-mini
OPENAI_KEY=<key>
OPENAI_ENDPOINT=https://<endpoint>.openai.azure.com/

*/

/*
    Create database credentials to store API key

    Replace <your-api-name> with the name of your Azure OpenAI service and <api-key> with the API key for the Azure OpenAI API
    https://github.com/Azure-Samples/azure-sql-db-vector-search/blob/main/Embeddings/T-SQL/01-store-openai-credentials.sql
*/
if not exists(select * from sys.symmetric_keys where [name] = '##MS_DatabaseMasterKey##')
begin
    create master key encryption by password = N'V3RYStr0NGP@ssw0rd!';
end
go
if exists(select * from sys.[database_scoped_credentials] where name = 'https://<endpoint>.openai.azure.com')
begin
	drop database scoped credential [https://<endpoint>.openai.azure.com];
end
create database scoped credential [https://<endpoint>.openai.azure.com]
with identity = 'HTTPEndpointHeaders', secret = '{"api-key": "<api-key>"}';
go

/*

    PROCEDURE: [dbo].[get_embeddings]

    DESCRIPTION:
    This stored procedure retrieves embeddings from an external REST endpoint using the specified model and input text.
    The embeddings are returned as a VECTOR(1536) output parameter.

    PARAMETERS:
    @model      - VARCHAR(MAX): The model to be used for generating embeddings.
    @text       - NVARCHAR(MAX): The input text for which embeddings are to be generated.
    @embedding  - VECTOR(1536) OUTPUT: The output parameter to store the generated embeddings.

    IMPLEMENTATION DETAILS:
    - The procedure constructs a URL for the REST endpoint using the provided model.
    - It prepares a JSON payload containing the input text and the dimension of the embedding.
    - The procedure invokes an external REST endpoint using the constructed URL and payload.
    - The response from the REST endpoint is parsed to extract the embedding array.
    - The extracted embedding array is cast to VECTOR(1536) and assigned to the output parameter @embedding.

    DEPENDENCIES:
    - dbo.sp_invoke_external_rest_endpoint: A stored procedure to invoke external REST endpoints.
    - JSON_OBJECT: A function to create JSON objects.
    - JSON_QUERY: A function to extract JSON arrays or objects from a JSON string.
*/

DROP PROCEDURE IF EXISTS [dbo].[get_embeddings]
GO

CREATE PROCEDURE [dbo].[get_embeddings]
(
    @model VARCHAR(MAX),
    @text NVARCHAR(MAX),
    @embedding VECTOR(1536) OUTPUT
)
AS
BEGIN

    SET NOCOUNT ON;

    DECLARE @retval INT, @response NVARCHAR(MAX);
    DECLARE @url VARCHAR(MAX);
    DECLARE @payload NVARCHAR(MAX) = JSON_OBJECT('input': @text, 'dimension': 1536);

    -- Set the @url variable with proper concatenation before the EXEC statement
    SET @url = 'https://<endpoint>.openai.azure.com/openai/deployments/' + @model + '/embeddings?api-version=2023-03-15-preview';

    EXEC dbo.sp_invoke_external_rest_endpoint 
        @url = @url,
        @method = 'POST',   
        @payload = @payload,   
        @credential = [https://<endpoint>.openai.azure.com],
        -- @headers = '{"Content-Type":"application/json", "api-key":"<api-key"}', 
        @response = @response OUTPUT;

    -- Use JSON_QUERY to extract the embedding array directly
    DECLARE @jsonArray NVARCHAR(MAX) = JSON_QUERY(@response, '$.result.data[0].embedding');
    
    SET @embedding = CAST(@jsonArray as VECTOR(1536));
END
GO

/*
    Stored Procedure: [dbo].[get_chat_completion]

    Description:
    This stored procedure interacts with the OpenAI API to get a chat completion based on the provided model, system message, and user prompt. 
    It handles retries in case of rate limiting and ensures that valid parameters are provided.

    Parameters:
    - @model (VARCHAR(MAX)): The model to be used for generating the chat completion.
    - @system_message (NVARCHAR(MAX)): The system message to be included in the chat context.
    - @user_prompt (NVARCHAR(MAX)): The user prompt to be included in the chat context.
    - @temperature (FLOAT): The temperature setting for the model, must be between 0 and 1.
    - @max_tokens (INT): The maximum number of tokens to be generated in the response.
    - @max_attempts (INT, default = 3): The maximum number of attempts to retry in case of rate limiting.
    - @chat_completion (NVARCHAR(MAX) OUTPUT): The output parameter to store the chat completion response.

    Error Handling:
    - Raises errors if required parameters are not provided or if they are invalid.
    - Handles rate limiting by retrying the request after the specified delay.
    - Raises an error if a valid response is not obtained after the maximum number of attempts.

    Usage:
    EXEC [dbo].[get_chat_completion] 
        @model = 'model_name', 
        @system_message = N'system message', 
        @user_prompt = N'user prompt', 
        @temperature = 0.7, 
        @max_tokens = 100, 
        @chat_completion = @output_variable OUTPUT;
*/

DROP PROCEDURE IF EXISTS [dbo].[get_chat_completion];
GO

CREATE PROCEDURE [dbo].[get_chat_completion]
(
    @model VARCHAR(MAX),
    @system_message NVARCHAR(MAX),
    @user_prompt NVARCHAR(MAX),
    @temperature FLOAT,
    @max_tokens INT,
    @max_attempts INT = 3,
    @chat_completion NVARCHAR(MAX) OUTPUT
)
AS
BEGIN

    SET NOCOUNT ON;

    BEGIN TRY
        DECLARE @retval INT, @response NVARCHAR(MAX);
        DECLARE @url NVARCHAR(MAX);
        DECLARE @payload NVARCHAR(MAX);
        DECLARE @attempts INT = 0;
        DECLARE @wait_time_ms INT = 5000;

        IF @model IS NULL OR @model = ''
        BEGIN
            RAISERROR('Model parameter must be provided.', 16, 1);
            RETURN;
        END

        IF @system_message IS NULL OR @system_message = ''
        BEGIN
            RAISERROR('System message must be provided.', 16, 1);
            RETURN;
        END

        IF @user_prompt IS NULL OR @user_prompt = ''
        BEGIN
            RAISERROR('User prompt must be provided.', 16, 1);
            RETURN;
        END

        IF @temperature IS NULL OR @max_tokens IS NULL
        BEGIN
            RAISERROR('Temperature and max tokens must be provided.', 16, 1);
            RETURN;
        END

        IF @temperature < 0 OR @temperature > 1
        BEGIN
            RAISERROR('Temperature must be between 0 and 1.', 16, 1);
            RETURN;
        END

        IF @max_tokens <= 0
        BEGIN
            RAISERROR('Max tokens must be greater than 0.', 16, 1);
            RETURN;
        END

        SET @url = N'https://<endpoint>.openai.azure.com/openai/deployments/' + @model + '/chat/completions?api-version=2023-05-15';

        SET @payload = JSON_OBJECT('messages': JSON_ARRAY(
                        JSON_OBJECT('role': 'system', 'content': @system_message),
                        JSON_OBJECT('role': 'user', 'content': @user_prompt)),
                        'temperature': @temperature,
                        'max_tokens': @max_tokens);

        WHILE @attempts < @max_attempts
        BEGIN
            BEGIN TRY
                SET @attempts = @attempts + 1;

                EXEC dbo.sp_invoke_external_rest_endpoint
                    @url = @url,
                    @method = 'POST',   
                    @payload = @payload,   
                    @credential = 'https://<endpoint>.openai.azure.com',
                    @response = @response OUTPUT;

                SET @chat_completion = JSON_VALUE(@response, '$.result.choices[0].message.content');
                IF (NOT @chat_completion IS NULL OR @chat_completion <> '')
                BEGIN
                    BREAK;
                END
                IF JSON_VALUE(@response, '$.result.error.code') = '429'
                BEGIN
                    DECLARE @retryAfter NVARCHAR(10);
                    SET @retryAfter = JSON_VALUE(@response, '$.response.headers."Retry-After"');
                    -- Declare a variable to store the Retry-After value as an integer
                    -- Convert the Retry-After value to an integer and add 1 second
                    DECLARE @retryAfterSeconds INT;
                    SET @retryAfterSeconds = CAST(@retryAfter AS INT) + 1;

                    -- Calculate hours, minutes, and seconds for the HH:MM:SS format
                    DECLARE @hours NVARCHAR(2), @minutes NVARCHAR(2), @seconds NVARCHAR(2);

                    SET @hours = RIGHT('0' + CAST(@retryAfterSeconds / 3600 AS NVARCHAR), 2);
                    SET @minutes = RIGHT('0' + CAST((@retryAfterSeconds % 3600) / 60 AS NVARCHAR), 2);
                    SET @seconds = RIGHT('0' + CAST(@retryAfterSeconds % 60 AS NVARCHAR), 2);

                    DECLARE @delay NVARCHAR(8);
                    SET @delay = @hours + ':' + @minutes + ':' + @seconds;

                    PRINT 'Rate limit error detected. Retry-After: ' + @delay + '. Attempt ' + CAST(@attempts AS NVARCHAR(10)) + '.';                    
                    WAITFOR DELAY @delay;
                END
            END TRY
            BEGIN CATCH
                THROW;
            END CATCH
        END
        IF @attempts >= @max_attempts AND (@chat_completion IS NULL OR @chat_completion = '')
        BEGIN
            RAISERROR('Failed to get a valid response after multiple attempts.', 16, 1);
            RETURN;
        END
        SET @chat_completion = REPLACE(REPLACE(@chat_completion, CHAR(13) + CHAR(10) + CHAR(13) + CHAR(10), CHAR(13) + CHAR(10)), CHAR(13) + CHAR(10) + CHAR(10), CHAR(13) + CHAR(10));
    END TRY
    BEGIN CATCH
        DECLARE @ErrorMessage2 NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();

        RAISERROR(@ErrorMessage2, @ErrorSeverity, @ErrorState);
    END CATCH
END
GO

/*

    PROCEDURE: dbo.add_summary_to_json_in_events_details__minute_agg

    DESCRIPTION:
    This stored procedure processes records in the `events_details__minute_agg` table that do not have a summary.
    It generates a summary and embeddings for each record and updates the table with these values.

    PARAMETERS:
    @system_message NVARCHAR(MAX) - The system message to be used for generating the summary.
    @model VARCHAR(MAX) - The model to be used for generating the summary.
    @temperature FLOAT - The temperature setting for the model.
    @max_tokens INT - The maximum number of tokens for the model.
    @max_attempts INT - The maximum number of attempts to generate the summary (default is 3).
    @match_id INT - The match ID to filter records (optional).

    PROCESS:
    1. Declares necessary variables for processing.
    2. Opens a cursor to iterate over records in `events_details__minute_agg` where the summary is NULL and optionally filtered by `match_id`.
    3. For each record:
       a. Calls `dbo.get_chat_completion` to generate a summary from the JSON data.
       b. Calls `dbo.get_embeddings` to generate embeddings for the summary using two different models.
       c. Updates the record in `events_details__minute_agg` with the generated summary and embeddings if the summary is not NULL or empty.
    4. Closes and deallocates the cursor.
*/

DROP PROCEDURE IF EXISTS dbo.add_summary_to_json_in_events_details__minute_agg
GO

CREATE PROCEDURE dbo.add_summary_to_json_in_events_details__minute_agg
    @system_message NVARCHAR(MAX),
    @model VARCHAR(MAX),
    @temperature FLOAT,
    @max_tokens INT,
    @max_attempts INT = 3,
    @match_id INT = NULL

AS
BEGIN

    SET NOCOUNT ON;

    DECLARE @json NVARCHAR(MAX);
    DECLARE @summary NVARCHAR(MAX);
    DECLARE @embedding_ada_002 VECTOR(1536);
    DECLARE @embedding_3_small VECTOR(1536);

    DECLARE @_match_id INT;
    DECLARE @period INT;
    DECLARE @minute INT;
    DECLARE @count INT;

    DECLARE @cursor CURSOR;

    SET @cursor = CURSOR FOR
    SELECT 
        match_id,
        period,
        minute,
        count,
        json_
    FROM
        events_details__minute_agg
    WHERE
        summary IS NULL
        and (@match_id IS NULL or match_id = @match_id);

    OPEN @cursor;
    FETCH NEXT FROM @cursor INTO @_match_id, @period, @minute, @count, @json;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- convert json to summary/script
        EXEC dbo.get_chat_completion @model = @model, @system_message = @system_message, @user_prompt = @json, 
            @temperature = @temperature, @max_tokens = @max_tokens,
            @max_attempts = @max_attempts,  @chat_completion = @summary OUTPUT;

        -- calculate embeddings
        EXEC dbo.get_embeddings @model = 'text-embedding-ada-002', @text = @summary, @embedding = @embedding_ada_002 OUTPUT;
        EXEC dbo.get_embeddings @model = 'text-embedding-3-small', @text = @summary, @embedding = @embedding_3_small OUTPUT;

        IF (NOT @summary IS NULL AND @summary <> '')
        BEGIN
            UPDATE events_details__minute_agg
            SET
                summary = @summary,
                embedding_ada_002 = @embedding_ada_002,
                embedding_3_small = @embedding_3_small
            WHERE
                match_id = @_match_id AND
                period = @period AND
                minute = @minute;
        END

        FETCH NEXT FROM @cursor INTO @_match_id, @period, @minute, @count, @json;
    END

    CLOSE @cursor;
    DEALLOCATE @cursor;
END
GO
/*
    Stored Procedure: dbo.add_summary_to_json_in_events_details__15secs_agg

    Description:
    This stored procedure processes records from the `events_details__15secs_agg` table that do not have a summary.
    It generates a summary and embeddings for each record and updates the table with these values.

    Parameters:
    - @system_message NVARCHAR(MAX): The system message to be used in the chat completion.
    - @model VARCHAR(MAX): The model to be used for generating the summary.
    - @temperature FLOAT: The temperature setting for the model.
    - @max_tokens INT: The maximum number of tokens for the model.
    - @max_attempts INT (default = 3): The maximum number of attempts for generating the summary.
    - @match_id INT (default = NULL): The match ID to filter records. If NULL, all records without a summary are processed.

    Internal Variables:
    - @json NVARCHAR(MAX): Stores the JSON data from the table.
    - @summary NVARCHAR(MAX): Stores the generated summary.
    - @embedding_ada_002 VECTOR(1536): Stores the embedding generated by the 'text-embedding-ada-002' model.
    - @embedding_3_small VECTOR(1536): Stores the embedding generated by the 'text-embedding-3-small' model.
    - @_match_id INT: Stores the match ID from the cursor.
    - @period INT: Stores the period from the cursor.
    - @minute INT: Stores the minute from the cursor.
    - @_15secs INT: Stores the 15-second interval from the cursor.
    - @count INT: Stores the count from the cursor.
    - @cursor CURSOR: Cursor for iterating over records in the `events_details__15secs_agg` table.

    Process:
    1. Opens a cursor to select records from `events_details__15secs_agg` where the summary is NULL and optionally filtered by match_id.
    2. Iterates over each record:
        a. Calls `dbo.get_chat_completion` to generate a summary from the JSON data.
        b. Calls `dbo.get_embeddings` to generate embeddings for the summary using two different models.
        c. Updates the record in `events_details__15secs_agg` with the generated summary and embeddings if the summary is not NULL or empty.
    3. Closes and deallocates the cursor.
*/

DROP PROCEDURE IF EXISTS dbo.add_summary_to_json_in_events_details__15secs_agg
GO

CREATE PROCEDURE dbo.add_summary_to_json_in_events_details__15secs_agg
    @system_message NVARCHAR(MAX),
    @model VARCHAR(MAX),
    @temperature FLOAT,
    @max_tokens INT,
    @max_attempts INT = 3,
    @match_id INT = NULL

AS
BEGIN

    SET NOCOUNT ON;

    DECLARE @json NVARCHAR(MAX);
    DECLARE @summary NVARCHAR(MAX);
    DECLARE @embedding_ada_002 VECTOR(1536);
    DECLARE @embedding_3_small VECTOR(1536);

    DECLARE @_match_id INT;
    DECLARE @period INT;
    DECLARE @minute INT;
    DECLARE @_15secs INT;
    DECLARE @count INT;

    DECLARE @cursor CURSOR;

    SET @cursor = CURSOR FOR
    SELECT 
        match_id,
        period,
        minute,
        _15secs,
        count,
        json_
    FROM
        events_details__15secs_agg
    WHERE
        summary IS NULL
        and (@match_id IS NULL or match_id = @match_id);

    OPEN @cursor;
    FETCH NEXT FROM @cursor INTO @_match_id, @period, @minute, @_15secs, @count, @json;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- convert json to summary/script
        EXEC dbo.get_chat_completion @model = @model, @system_message = @system_message, @user_prompt = @json, 
            @temperature = @temperature, @max_tokens = @max_tokens,
            @max_attempts = @max_attempts,  @chat_completion = @summary OUTPUT;

        -- calculate embeddings
        EXEC dbo.get_embeddings @model = 'text-embedding-ada-002', @text = @summary, @embedding = @embedding_ada_002 OUTPUT;
        EXEC dbo.get_embeddings @model = 'text-embedding-3-small', @text = @summary, @embedding = @embedding_3_small OUTPUT;

        IF (NOT @summary IS NULL AND @summary <> '')
        BEGIN
            UPDATE events_details__15secs_agg
            SET
                summary = @summary,
                embedding_ada_002 = @embedding_ada_002,
                embedding_3_small = @embedding_3_small
            WHERE
                match_id = @_match_id AND
                period = @period AND
                minute = @minute AND
                _15secs = @_15secs;
        END

        FETCH NEXT FROM @cursor INTO @_match_id, @period, @minute, @_15secs, @count, @json;
    END

    CLOSE @cursor;
    DEALLOCATE @cursor;
END

GO
/*

    PROCEDURE: dbo.rebuild_embeddings_in_events_details__15secs_agg

    DESCRIPTION:
    This stored procedure rebuilds the embeddings in the 'events_details__15secs_agg' table for a specific match.
    It iterates through records with non-null summaries and null embeddings, calculates embeddings using the 
    'text-embedding-ada-002' and 'text-embedding-3-small' models, and updates the table with the new embeddings.

    PARAMETERS:
    @match_id (INT) - The ID of the match for which embeddings need to be rebuilt.
    @max_attempts (INT) - The maximum number of attempts for processing (default is 3).

    DECLARATIONS:
    @summary (NVARCHAR(MAX)) - Stores the summary text from the table.
    @period (INT) - Stores the period value from the table.
    @minute (INT) - Stores the minute value from the table.
    @_15secs (INT) - Stores the 15 seconds interval value from the table.
    @embedding_ada_002 (VECTOR(1536)) - Stores the embedding calculated using the 'text-embedding-ada-002' model.
    @embedding_3_small (VECTOR(1536)) - Stores the embedding calculated using the 'text-embedding-3-small' model.
    @cursor (CURSOR) - Cursor for iterating through the records in the table.

    PROCESS:
    1. Initialize a cursor to select records with non-null summaries and null embeddings for the specified match.
    2. Open the cursor and fetch the first record.
    3. Loop through each record fetched by the cursor:
       a. Calculate embeddings using the specified models.
       b. Update the table with the new embeddings.
       c. Fetch the next record.
    4. Close and deallocate the cursor.
*/

DROP PROCEDURE IF EXISTS dbo.rebuild_embeddings_in_events_details__15secs_agg
GO

CREATE PROCEDURE dbo.rebuild_embeddings_in_events_details__15secs_agg
    @match_id INT,
    @max_attempts INT = 3

AS
BEGIN

    SET NOCOUNT ON;

    DECLARE @summary NVARCHAR(MAX);
    DECLARE @period INT;
    DECLARE @minute INT;
    DECLARE @_15secs INT;

    DECLARE @embedding_ada_002 VECTOR(1536);
    DECLARE @embedding_3_small VECTOR(1536);

    DECLARE @cursor CURSOR;

    SET @cursor = CURSOR FOR
    SELECT 
        period,
        minute,
        _15secs,
        summary
    FROM
        events_details__15secs_agg
    WHERE
        not summary IS NULL
        and embedding_ada_002 IS NULL
        and embedding_3_small IS NULL
        and match_id = @match_id;

    OPEN @cursor;
    FETCH NEXT FROM @cursor INTO @period, @minute, @_15secs, @summary;

    WHILE @@FETCH_STATUS = 0
    BEGIN

        -- calculate embeddings
        EXEC dbo.get_embeddings @model = 'text-embedding-ada-002', @text = @summary, @embedding = @embedding_ada_002 OUTPUT;
        EXEC dbo.get_embeddings @model = 'text-embedding-3-small', @text = @summary, @embedding = @embedding_3_small OUTPUT;

        UPDATE events_details__15secs_agg
        SET
            embedding_ada_002 = @embedding_ada_002,
            embedding_3_small = @embedding_3_small
        WHERE
            match_id = @match_id AND
            period = @period AND
            minute = @minute AND
            _15secs = @_15secs;

        FETCH NEXT FROM @cursor INTO @period, @minute, @_15secs, @summary;
    END

    CLOSE @cursor;
    DEALLOCATE @cursor;
END
