/*

    DESCRIPTION:
    This script is a template for summarizing JSON data of a football match in prose format. It uses a system message to instruct the summarization model on how to describe the events in English, focusing on detailed actions ordered minute by minute. The script highlights special events such as goals, missed goals, shots on goal, and goalkeeper saves, mentioning the time and score changes if applicable. The summary is generated in a commentator style, mentioning players and using the word "keeper" instead of "goalkeeper". The script concludes with a brief summary sentence.

    PARAMETERS:
    - @system_message: The instruction message for the summarization model.
    - @model: The model used for summarization (e.g., 'gpt-4o-mini').
    - @temperature: The temperature setting for the model, affecting the randomness of the output.
    - @max_tokens: The maximum number of tokens for the model's output.
    - @match_id: The ID of the match to be summarized.

    USAGE:
    Uncomment the desired exec statement to run the summarization for either minute-by-minute aggregation or 15-second aggregation of events. Adjust the parameters as needed for different matches or summarization requirements.
*/


declare @system_message nvarchar(max);

set @system_message = N'Describe the message in English. It is a football match, and I am providing the detailed actions in Json format ordered minute by minute how action how they happenned.
    By using the id, and related_events columns you can cross-relate events. There may be some hierachies. Mention the players in the script.
    Do not invent any information. Do relate stick to the data. 
    In special events like: goal sucessful, goal missed, shoots to goal, and goalkeeper saves relate like a commentator highlighting the action mentioning time, and score changes if apply.
    Relate in prose format. Use the word keeper instead of goalkeeper.
    This is a portion of the event; it does not represent the whole match.
    Do not make intro like "In the early moments of the match", "In the openning", etc. Just relate the action.
    At the end include one sentence as a brief description of what happened starting with "Summary:"
    This is the Json data: ';

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
    @max_tokens = 5000,
    @match_id = 3943043;

