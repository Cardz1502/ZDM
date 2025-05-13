BUILD THE CONTAINER (OCTOPRINT-API.PY)

docker build -f Dockerfile.local -t octoprint-local .    

RUN THE CONTAINER

docker run -d --name octoprint-local octoprint-local                
