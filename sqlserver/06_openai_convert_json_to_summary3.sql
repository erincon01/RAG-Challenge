/*
    DESCRIPTION:
    This script is a template for summarizing JSON data in prose format for football matches. 
    It generates a summary of play-by-play commentaries, focusing on the most relevant actions 
    such as goals, penalties, injuries, and cards only if players are sent off. The summary 
    is created using the specified model and parameters.

    FOR THIS CASE, WE PROCESS ALL THE GAMES THAT SPAIN PLAYED IN THE UEFA EURO 2024.

    PARAMETERS:
    - @system_message: The message template that guides the summary generation.
    - @model: The AI model used for generating the summary (e.g., 'gpt-4o-mini').
    - @temperature: The temperature setting for the model, controlling the randomness of the output.
    - @max_tokens: The maximum number of tokens (words) for the generated summary.
    - @match_id: The ID of the football match for which the summary is being generated.

    USAGE:
    Uncomment the appropriate EXEC statement to generate a summary for a specific match 
    using either minute-by-minute or 15-second aggregation of events.
*/

DECLARE @match_id INT;
DECLARE @system_message NVARCHAR(MAX);

-- Configure the message for the system, including the generic text and the current match_id
SET @system_message = N'Make a summary of this batch of play-by-play commentaries.
            It is a football match, and I am providing the detailed actions in prose ordered minute by minute.
            Use minutes in numbers, do not use seconds. Mention timing only for relevant actions like goals, penalties, and injuries, and cards. 
            Do not include introduction or conclusion, just the actions. Do not use use the term match because we know it is data from football match.
            Do not invent any information, relate stick to the data, and do not include any personal opinion.
            Relate in prose format. this is the text:
            ';

-- Define the cursor for the match_id query
DECLARE match_cursor CURSOR FOR
    SELECT DISTINCT matches.match_id
    FROM matches
    LEFT JOIN events_details__15secs_agg ed ON matches.match_id = ed.match_id
    WHERE competition_name = 'UEFA Euro'
      AND season_name = '2024'
      AND (
            (home_team_name = 'Spain' OR away_team_name = 'Spain') or
            (home_team_name = 'Spain' and away_team_name = 'England') or

            (home_team_name = 'Spain' and away_team_name = 'Germany') or
            (home_team_name = 'Netherlands' and away_team_name = 'England') or

            (home_team_name = 'Spain' and away_team_name = 'France') or
            (home_team_name = 'Netherlands' and away_team_name = 'Turkey') or
            (home_team_name = 'Portugal' and away_team_name = 'France') or
            (home_team_name = 'England' and away_team_name = 'Switzerland')
        )
      AND ed.json_ IS NOT NULL
      AND ed.summary IS NULL;

-- Open the cursor
OPEN match_cursor;

-- Fetch the first match_id
FETCH NEXT FROM match_cursor INTO @match_id;

-- Iterate through each fetched match_id
WHILE @@FETCH_STATUS = 0
BEGIN

    -- Execute the stored procedure to add the summary
    EXEC dbo.add_summary_to_json_in_events_details__15secs_agg
        @system_message = @system_message,
        @model = 'gpt-4o-mini',
        @temperature = 0.1,
        @max_tokens = 7500,
        @match_id = @match_id;

    PRINT 'Processed match_id: ' + CAST(@match_id AS VARCHAR);

    -- Fetch the next match_id
    FETCH NEXT FROM match_cursor INTO @match_id;
END;

-- Close and deallocate the cursor
CLOSE match_cursor;
DEALLOCATE match_cursor;
