BUILD THE CONTAINER (OCTOPRINT-API.PY)

sudo docker build -f Dockerfile.local -t octoprint-local .    

RUN THE CONTAINER

sudo docker run -d --restart always --name octoprint-local octoprint-local                

sudo docker stop octoprint-local
sudo docker rm octoprint-local
sudo docker logs -f octoprint-local
