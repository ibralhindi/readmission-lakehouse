# Extend the official Airflow image with the providers our DAG needs.
# Pin to the same version the compose file uses (check step 2).
FROM apache/airflow:3.2.1

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
