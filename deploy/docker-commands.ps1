
# remove image
docker rmi rag_challenge

# create image
docker build -f dockerfile -t rag-challenge:v1 .

# tag the image
docker tag rag_challenge acrerincon01.azurecr.io/rag_challenge:latest

# create the image
docker run --name rag_challenge --env-file .env --network docker_network -p 8501:8501 rag_challenge:v1

# running containers
docker ps
