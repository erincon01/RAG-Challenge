
# path and build the image

cd C:\Users\erincon\Sources\_personal\RAG-Challenge
docker build -f .devcontainer/dockerfile -t rag-challenge:v1 .

# set variables

$subscriptionId = "subscription-guid"
$resourceGroupName = "rg-erincon01"
$registryName = "ragchallengecr"
$location = "eastus"
$sku = "Basic"

$containerName = "rag-vector-container"
$image = "rag-challenge"
$dnsNameLabel = "sql-vector"
$imageTag = "v1"  
$cpu = 2
$memory = 8

###########################################################################################################
###########################################################################################################

# environment variables (COPY, PASTE, AND add $ to the beginning of each line from the .env file)

#################### ADD $ TO THE BEGINNING OF EACH LINE ##################################################

$BASE_URL="https://github.com/statsbomb/open-data/raw/master/data"
$REPO_OWNER="statsbomb"
$REPO_NAME="open-data"
$LOCAL_FOLDER="./data"
######### ETC... ###########################################################################################

###########################################################################################################
###########################################################################################################

# login to azure
az login 
Set-AzContext -SubscriptionId $subscriptionId

# create the container registry and push the image
New-AzContainerRegistry -ResourceGroupName $resourceGroupName -Name $registryName -Sku $sku -Location $location
az acr update -n $registryName --admin-enabled true

az acr login --name $registryName

docker tag "${image}:${imageTag}" "${registryName}.azurecr.io/${image}:${imageTag}"
docker push "${registryName}.azurecr.io/${image}:${imageTag}"

## list images and tags in the container registry
# az acr repository list --name $registryName --output table

# get the credentials and store them in variables
$acrCredentials = az acr credential show --name ragchallengecr | ConvertFrom-Json
$registryUsername = $acrCredentials.username
$registryPassword = $acrCredentials.passwords[0].value

## remove the container
# az container delete --resource-group $resourceGroupName --name $containerName --yes

# create the container
az container create `
    --resource-group $resourceGroupName `
    --location $location `
    --name $containerName `
    --image "${registryName}.azurecr.io/${image}:${imageTag}" `
    --cpu $cpu `
    --memory $memory `
    --ip-address public `
    --registry-login-server "${registryName}.azurecr.io" `
    --registry-username $registryUsername `
    --registry-password $registryPassword `
    --dns-name-label $dnsNameLabel `
    --ports 80 `
    --command-line "streamlit run /app/app.py --server.port=80 --server.headless=true" `
    --environment-variables  `
        BASE_URL=$BASE_URL `
        REPO_OWNER=$REPO_OWNER `
        REPO_NAME=$REPO_NAME `
        LOCAL_FOLDER=$LOCAL_FOLDER `
        DB_SERVER_AZURE=$DB_SERVER_AZURE `
        DB_NAME_AZURE=$DB_NAME_AZURE `
        DB_USER_AZURE=$DB_USER_AZURE `
        DB_SERVER_AZURE_POSTGRES=$DB_SERVER_AZURE_POSTGRES `
        DB_NAME_AZURE_POSTGRES=$DB_NAME_AZURE_POSTGRES `
        DB_USER_AZURE_POSTGRES=$DB_USER_AZURE_POSTGRES `
        OPENAI_MODEL=$OPENAI_MODEL `
        OPENAI_MODEL2=$OPENAI_MODEL2 `
        OPENAI_ENDPOINT=$OPENAI_ENDPOINT `
    --secure-environment-variables `
        DB_PASSWORD_AZURE=$DB_PASSWORD_AZURE `
        DB_PASSWORD_AZURE_POSTGRES=$DB_PASSWORD_AZURE_POSTGRES `
        OPENAI_KEY=$OPENAI_KEY

# check the status of the container
az container show --resource-group $resourceGroupName --name $containerName --query instanceView.state
az container show --resource-group $resourceGroupName --name $containerName --query ipAddress.ip -o tsv
az container list --query "[].{Name:name, FQDN:ipAddress.ip}" --output table

az container exec --resource-group $resourceGroupName --name $containerName --exec-command "/bin/bash"
az container exec --resource-group $resourceGroupName --name $containerName --exec-command "ls"
