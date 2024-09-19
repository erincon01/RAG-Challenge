/*

    DESCRIPTION:
    This script is a template for summarizing JSON data in prose format for football matches. 
    It generates a summary of play-by-play commentaries, focusing on the most relevant actions 
    such as goals, penalties, injuries, and cards only if players are sent off. The summary 
    is created using the specified model and parameters.

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

declare @system_message nvarchar(max);

set @system_message = N'Make a summary of this batch of play-by-play commentaries.
             It is a football match, and I am providing the detailed actions in prose ordered minute by minute.
             Include the most relevant actions such as goals, penalties, and injuries, and cards only if players are sent off. 
             Do not invent any information, relate stick to the data, and do not include any personal opinion. 
             Relate in prose format. this is the text:
             ';

    -- Euro Final 2024     : England - Spain match_id: 3943043
    -- FIFA World CUP 2022 : France - Argentina match_id: 3869685

/*
exec dbo.add_summary_to_json_in_events_details__minute_agg
    @system_message = @system_message,
    @model = 'gpt-4o-mini',
    @temperature = 0.1,
    @max_tokens = 7500,
    @match_id = 3869685;
*/

exec dbo.add_summary_to_json_in_events_details__15secs_agg
    @system_message = @system_message,
    @model = 'gpt-4o-mini',
    @temperature = 0.1,
    @max_tokens = 7500,
    @match_id = 3943043;
