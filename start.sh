#!/bin/bash

# Iniciar o opcua_server.py em background
python /app/opcua_server.py &

# Iniciar o octoprint-api.py em foreground
python /app/octoprint-api.py