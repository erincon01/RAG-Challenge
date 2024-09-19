
-- sandbox for testing out native vector search in SQL Azure Database

/*
DECLARE @e VECTOR(1536);
DECLARE @string nvarchar(max) = '<search_string>'

EXEC dbo.get_embeddings @model = '<embedding_model>', @text = @string, @embedding = @e OUTPUT;

SELECT TOP (<top_n>) 
    VECTOR_DISTANCE('<search_type>', @e, <embedding_column_name>) AS distance, *
from <table> 
ORDER BY 1 <ASC|DESC>;
*/

-- text-embedding-3-small
DECLARE @e_3small VECTOR(1536);
DECLARE @string nvarchar(max) = 
    'Which players recorded the highest number of carries and passes in both halves, 
    and how did their performances influence the overall strategies of the teams?'

EXEC dbo.get_embeddings @model = 'text-embedding-3-small', @text = @string, @embedding = @e_3small OUTPUT;

SELECT TOP (10) 
    VECTOR_DISTANCE('cosine', @e_3small, embedding_3_small) AS distance_cosine_3_small, *
from events_details__15secs_agg where match_id = 3943043 
ORDER BY 1;

SELECT TOP (10) 
    VECTOR_DISTANCE('euclidean', @e_3small, embedding_3_small) AS distance_euclidean_3_small, *
from events_details__15secs_agg where match_id = 3943043 
ORDER BY 1;

SELECT TOP (10) 
    VECTOR_DISTANCE('dot', @e_3small, embedding_3_small) AS distance_dot_3_small, *
from events_details__15secs_agg
where match_id = 3943043 
ORDER BY 1 desc;
GO

-- text-embedding-ada-002
DECLARE @e_ada002 VECTOR(1536);
DECLARE @string nvarchar(max) = 'Which players recorded the highest number of carries and passes in both halves, and how did their performances influence the overall strategies of the teams?'

EXEC dbo.get_embeddings @model = 'text-embedding-ada-002', @text = @string, @embedding = @e_ada002 OUTPUT;

SELECT TOP (10) 
    VECTOR_DISTANCE('cosine', @e_ada002, embedding_ada_002) AS distance_cosine_ada002, *
from events_details__15secs_agg where match_id = 3943043
ORDER BY 1;

SELECT TOP (10) 
    VECTOR_DISTANCE('euclidean', @e_ada002, embedding_ada_002) AS distance_euclidean_ada002, *
from events_details__15secs_agg where match_id = 3943043
ORDER BY 1;

SELECT TOP (10) 
    VECTOR_DISTANCE('dot', @e_ada002, embedding_ada_002) AS distance_dot_ada002, *
from events_details__15secs_agg where match_id = 3943043
ORDER BY 1 desc;

