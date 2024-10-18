# create image
docker build -t rag_challenge .

# tag the image
docker tag rag_challenge acrerincon01.azurecr.io/rag_challenge:latest

# remove image
docker rmi rag_challenge

# create network
docker network create docker_network

# connect existing container to network
docker network connect docker_network postgres18

# inspect network 
docker network inspect docker_network

# create the image
docker run --name rag_challenge --env-file .env --network docker_network -p 8501:8501 rag_challenge

# running containers
docker ps
