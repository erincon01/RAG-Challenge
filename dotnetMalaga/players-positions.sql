
DROP TABLE IF EXISTS player_positions;
GO

CREATE TABLE player_positions (
  player_name NVARCHAR(100) NOT NULL,
  position VECTOR(2) NOT NULL
);

INSERT INTO player_positions VALUES
('Unai Simón', '[5, 30]'),

('Dani Carvajal', '[20, 10]'),
('Aymeric Laporte', '[15, 20]'),
('Robin Le Normand', '[15, 40]'),
('Marc Cucurella', '[20, 50]'),

('Rodri', '[25, 30]'),
('Fabián', '[30, 40]'),
('Dani Olmo', '[30, 20]'),

('Lamine Yamal', '[40, 13]'),
('Morata', '[45, 30]'),
('Nico Williams', '[40, 47]');
GO

SELECT * FROM player_positions;

-- Calculate the distance between two players using the Euclidean, Cosine, and Dot Product similarity measures
-- pick Morata positition and compare with the rest of the players
declare @morata_position VECTOR(2) = '[45, 30]';
SELECT 
    CAST(VECTOR_DISTANCE('euclidean', @morata_position, position) AS DECIMAL(10,3)) AS euclidean,
    CAST(VECTOR_DISTANCE('cosine', @morata_position, position) AS DECIMAL(10,3)) AS cosine,
    VECTOR_DISTANCE('dot', @morata_position, position) AS negative_dot_product,
    player_name
    from player_positions
    where player_name in ('Lamine Yamal', 'Morata', 'Rodri', 'Dani Carvajal')
    order by cosine
GO

declare @morata_position VECTOR(2) = '[45, 30]';
SELECT 
    VECTOR_DISTANCE('euclidean', position, @morata_position),
    VECTOR_DISTANCE('cosine', position, @morata_position),
    VECTOR_DISTANCE('dot', position, @morata_position),
    player_name
    from player_positions
    where player_name in 
    ('Lamine Yamal', 'Morata', 'Rodri', 'Dani Carvajal');

