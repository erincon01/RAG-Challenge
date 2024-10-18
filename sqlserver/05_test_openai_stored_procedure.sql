/*
    This script performs a smoke test for the model by testing embeddings and chat completion functionalities.

    Embeddings Test:
    - Declares two vector variables, @e_ada002 and @e_3small, each of size 1536.
    - Initializes a string variable @string with a sample text.
    - Executes the stored procedure dbo.get_embeddings twice to get embeddings for the given text using two different models ('text-embedding-ada-002' and 'text-embedding-3-small').
    - Outputs the embeddings for comparison.

    Chat Completion Test:
    - Declares variables for the model, prompt, system message, and chat completion.
    - Sets the system message with instructions for describing a football match event in English.
    - Retrieves a JSON-formatted prompt from the events_details__minute_agg table for a specific match and minute.
    - Executes the stored procedure dbo.get_chat_completion to generate a chat completion based on the provided model, system message, and user prompt.
    - Prints the generated chat completion.

    Note:
    - The script includes a sample output of the chat completion for a football match event at the 85th minute.
    - Comments highlight the importance of considering the overall context of the match when splitting data by minutes.
*/


DECLARE @e_ada002 VECTOR(1536);
DECLARE @e_3small VECTOR(1536);
DECLARE @string nvarchar(max) = 'Mikel Oyarzabal scored the goal at minute 85!'

EXEC dbo.get_embeddings @model = 'text-embedding-ada-002', @text = @string, @embedding = @e_ada002 OUTPUT;
EXEC dbo.get_embeddings @model = 'text-embedding-3-small', @text = @string, @embedding = @e_3small OUTPUT;

SELECT @e_ada002, @e_3small;
GO

-- chat_completion

declare @model nvarchar(max) = 'gpt-4o-mini';
declare @prompt nvarchar(max);
declare @system_message nvarchar(max);
declare @chat_completion nvarchar(max);

set @system_message = N'Describe the message in English. It is a football match, and I am providing the detailed actions in Json format ordered minute by minute how action how they happenned.
    By using the id, and related_events columns you can cross-relate events. There may be some hierachies. Mention the players in the script.
    Do not invent any information. Do relate stick to the data. 
    In special events like: goal sucessful, goal missed, shoots to goal, and goalkeeper saves relate like a commentator highlighting the action mentioning time, and score changes if apply.
    Relate in prose format. Use the word keeper instead of goalkeeper.
    Do not make intro like "In the early moments of the match", "In the openning", etc. Just start with the action.
    At the end include one sentence as a brief description of what happened starting with "Summary:"
    This is the Json data: ';


    -- Euro Final 2024     : England - Spain match_id: 3943043
    -- FIFA World CUP 2022 : France - Argentina match_id: 3869685

select top 1 @prompt = json_
from events_details__minute_agg
where match_id = 3943043 and minute = 85;

EXEC dbo.[get_chat_completion] @model = @model, @system_message = @system_message, @user_prompt = @prompt, @temperature = 0.1, @max_tokens = 7500, @chat_completion = @chat_completion OUTPUT;

print @chat_completion

/*
    At 85 minutes into the match, Jordan Pickford, the keeper for England, initiated a play by passing the ball to Kyle Walker with a ground pass from his position. 
    Walker received the ball and carried it forward under pressure from Spain's Daniel Olmo Carvajal. 
    Walker skillfully dribbled past Olmo and continued his run, eventually passing to Bukayo Saka. Saka then carried the ball before making a pass to John Stones, who received 
    it cleanly. Stones moved the ball to Marc Guehi, who then passed it to Declan Rice. Rice, maintaining possession, passed back to Guehi, who continued to advance the play.
    Guehi then made a long pass to Pickford, who received it and carried the ball briefly before passing it back to Guehi again. Guehi continued to move the ball forward, 
    passing it to Ollie Watkins, who attempted to receive it but was unable to complete the pass.
    Spain's Daniel Carvajal then took a throw-in, passing to Aymeric Laporte, who received the ball and carried it forward. Laporte passed to Fabián Ruiz Peña, who then made 
    a pass to Daniel Olmo Carvajal. Olmo carried the ball and passed it to Mikel Oyarzabal, who received it and made a pass to Marc Cucurella Saseta.
    Cucurella, under pressure from Kyle Walker, managed to pass to Oyarzabal, who then took a shot at goal. The shot found the back of the net, resulting in a goal for Spain, 
    with the score now reflecting a change in favor of Spain.
    Summary: Spain scored a goal through Mikel Oyarzabal after a series of passes, taking advantage of England's defensive lapses, bringing the score to 1-0.

    -- SPLITING DATA IN MINUTES HIDES THE OVERAL CONTEXT OF THE MATCH.
    -- see that minute 85 summary says result is 1-0, but the match ended 2-1
    -- system message should be more clear to relate actions in the period, not aggregate overal match result
*/


