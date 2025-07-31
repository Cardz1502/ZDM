FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "models_aux.py"]
EXPOSE 5000
EXPOSE 5002
EXPOSE 5004