
# connect to the subscription
az login
az account set --subscription "your_subscription_guid"

# create the images container
az acr create --resource-group rg-name --name acr_admin_user --sku Basic

az acr login -n acr_admin_user

# add the image to the container
docker push acr_admin_user.azurecr.io/rag_challenge

# create the container
  az container create `
     --resource-group rg-name `
    --name ragchallenge01 `
    --image acr_admin_user.azurecr.io/rag_challenge `
    --dns-name-label ragchallenge01 `
    --ports 8501 `
    --registry-username acr_admin_user `
    --registry-passwor password_value `
    --environment-variables  `
        BASE_URL=https://github.com/statsbomb/open-data/raw/master/data `
        REPO_OWNER=statsbomb `
        REPO_NAME=open-data `
        LOCAL_FOLDER=./data `
        DB_SERVER=postgres18 `
        DB_NAME=statsbomb_all `
        DB_USER=postgres `
        DB_SERVER_AZURE=servername.postgres.database.azure.com `
        DB_NAME_AZURE=statsbomb01azr `
        DB_USER_AZURE=postgres `
        OPENAI_MODEL=gpt-4o-mini `
        OPENAI_ENDPOINT=https://endpoint.openai.azure.com/ `
    --secure-environment-variables `
        DB_PASSWORD=your_password `
        DB_PASSWORD_AZURE=your_password `
        OPENAI_KEY=your_key `
