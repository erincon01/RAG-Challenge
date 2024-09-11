
-- configure the extensions in the server

SELECT * FROM pg_available_extensions where name like '%vector%' or  name like '%azure%';

SHOW azure.extensions;

CREATE EXTENSION azure_local_ai;
CREATE EXTENSION vector;

SELECT azure_local_ai.get_setting('intra_op_parallelism');
SELECT azure_local_ai.get_setting('inter_op_parallelism');
SELECT azure_local_ai.get_setting('spin_control');

ALTER EXTENSION azure_local_ai UPDATE;
ALTER EXTENSION vector UPDATE;

-- optionally, enable azure_open_ai if you need to use open_ai embeddings

CREATE EXTENSION azure_ai;

select azure_ai.set_setting('azure_openai.endpoint','https://<endpoint>.openai.azure.com'); 
select azure_ai.set_setting('azure_openai.subscription_key', 'key');

select azure_ai.get_setting('azure_openai.endpoint');
select azure_ai.get_setting('azure_openai.subscription_key');
select azure_ai.version();

ALTER EXTENSION azure_ai UPDATE;

-- be careful with this ALTER because it persissts the data in the table immediately
-- takes long time due to embeding generation
