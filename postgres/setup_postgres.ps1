


# Using embeddings in postgresql requires the following extensions to be installed:

# - vector
# - azure_ai
# - azure_local_ai

# can be installed from the portal: https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/generative-ai-azure-overview
# can be installed using the az cli: https://learn.microsoft.com/en-us/cli/azure/postgres/flexible-server?view=azure-cli-latest

# az cli command to install the extensions:

az login

az postgres flexible-server parameter set `
    --resource-group <rg>  `
    --server-name <server> `
    --subscription <subs_id> `
    --name azure.extensions `
    --value vector,azure_ai,azure_local_ai



    # Message like this should be showed:

    # configuration_name is not a known attribute of class <class 'azure.mgmt.rdbms.postgresql_flexibleservers.models._models_py3.Configuration'> and will be ignored
    # {
    #   "allowedValues": ",address_standardizer,address_standardizer_data_us,amcheck,azure_ai,azure_local_ai,azure_storage,bloom,btree_gin,btree_gist,citext,cube,dblink,dict_int,dict_xsyn,earthdistance,fuzzystrmatch,hstore,hypopg,intagg,intarray,isn,lo,login_hook,ltree,orafce,pageinspect,pg_buffercache,pg_cron,pg_freespacemap,pg_hint_plan,pg_partman,pg_prewarm,pg_repack,pg_squeeze,pg_stat_statements,pg_trgm,pg_visibility,pgaudit,pgcrypto,pglogical,pgrowlocks,pgstattuple,plpgsql,plv8,postgis,postgis_raster,postgis_sfcgal,postgis_tiger_geocoder,postgis_topology,postgres_fdw,postgres_protobuf,semver,session_variable,sslinfo,tablefunc,tds_fdw,timescaledb,tsm_system_rows,tsm_system_time,unaccent,uuid-ossp,vector",
    #   "dataType": "Set",
    #   "defaultValue": "",
    #   "description": "Specifies which extensions are allowed to be created in the server.",
    #   "documentationLink": "https://go.microsoft.com/fwlink/?linkid=2274269",
    #   "id": "/xxxxxxxxxxxxxxxxxx/azure.extensions",
    #   "isConfigPendingRestart": false,
    #   "isDynamicConfig": true,
    #   "isReadOnly": false,
    #   "name": "azure.extensions",
    #   "resourceGroup": "rg-erincon01",
    #   "source": "user-override",
    #   "systemData": null,
    #   "type": "Microsoft.DBforPostgreSQL/flexibleServers/configurations",
    #   "unit": null,
    #   "value": "vector,azure_local_ai,azure_ai"
    # }
