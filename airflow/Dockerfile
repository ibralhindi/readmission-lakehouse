# Extend the official Airflow image with the providers our DAG needs.
# Pin the base image here; docker-compose.yaml builds this local Dockerfile.
FROM apache/airflow:3.2.1

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
