

drop table if EXISTS texts;
create table texts (doc text);

insert into texts values ('01 | ball receipt | 40:46 | Aymeric Laporte | Receives ball | Left Center Back | None | Daniel Carvajal | None');
insert into texts values ('02 | carry | 40:46 | Aymeric Laporte | Carries ball | Left Center Back | None | None | None');
insert into texts values ('03 | ball receipt | 40:30 | Jordan Pickford | Receives ball | gkeeper | None | Marc Guehi | None');
insert into texts values ('04 | carry | 40:30 | Jordan Pickford | Carries ball | gkeeper | None | None | None');
insert into texts values ('05 | pass | 40:32 | Jordan Pickford | Pass to Marc Guehi | gkeeper | Ground Pass | None | None');
insert into texts values ('06 | ball receipt | 40:34 | Marc Guehi | Receives ball | Left Center Back | None | Jordan Pickford | None');
insert into texts values ('07 | carry | 40:34 | Marc Guehi | Carries ball | Left Center Back | None | None | None');
insert into texts values ('08 | pass | 40:36 | Marc Guehi | Pass to Ollie Watkins | Left Center Back | missed Goal | None | None');
insert into texts values ('09 | ball receipt | 40:40 | Ollie Watkins | Receives ball | Center Forward | Goal | Marc Guehi | None');
insert into texts values ('10 | pass | 40:43 | Daniel Carvajal | Throw-in to Aymeric Laporte | Right Back | Low Pass | None | None');
insert into texts values ('11 | pass | 40:47 | Aymeric Laporte | Pass to Fabián Ruiz Peña | Left Center Back | Ground Pass | None | None');
insert into texts values ('12 | carry | 40:50 | Daniel Olmo Carvajal | Carries ball | Center Attacking Midfield | None | None | None');
insert into texts values ('13 | pass | 40:52 | Daniel Olmo Carvajal | Pass to Mikel Oyarzabal Ugarte | Center Attacking Midfield | Ground Pass | None | None');
insert into texts values ('14 | ball receipt | 40:53 | Mikel Oyarzabal Ugarte | Receives ball | Center Forward | None | Daniel Olmo Carvajal | None');
insert into texts values ('15 | shot | 40:56 | Mikel Oyarzabal Ugarte | **Goal** | Center Forward | Open Play | None | None');
insert into texts values ('16 | gkeeper | 40:57 | Jordan Pickford | Goal conceded | gkeeper | None | Mikel Oyarzabal Ugarte | No Touch');


ALTER TABLE texts
ADD COLUMN e1 vector(384) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', doc)::vector) STORED; 

--ALTER TABLE texts
--ADD COLUMN e2 VECTOR(1536) --ADAD embeddings are 1536 dimensions
--GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-ada-002', doc)::vector) STORED;


-- select * from texts;

-- Retrieve similarities. NIP
SELECT doc
    , e1 <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal scored')::vector AS nip_1
--    , e2 <#> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS nip_2
FROM texts
ORDER BY nip_1
LIMIT 10;
