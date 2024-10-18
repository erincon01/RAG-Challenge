/*

    Description:
    This optional stored procedure is used to rebuild the embeddings for a specific match_id.
    It sets the embedding_ada_002 and embedding_3_small columns to null for the given match_id
    in the dbo.events_details__15secs_agg table, and then calls the 
    dbo.rebuild_embeddings_in_events_details__15secs_agg procedure to regenerate the embeddings.

    Example Match IDs:
    - Euro Final 2024: England - Spain (match_id: 3943043)
    - FIFA World CUP 2022: France - Argentina (match_id: 3869685)

    Parameters:
    - @match_id (INT): The ID of the match for which embeddings need to be rebuilt.
*/


declare @match_id INT = 3943043;

update dbo.events_details__15secs_agg
set 
    embedding_ada_002 = null,
    embedding_3_small = null

WHERE match_id = @match_id;

exec dbo.rebuild_embeddings_in_events_details__15secs_agg
    @match_id = @match_id;
