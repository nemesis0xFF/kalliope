FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 curl bzip2 && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# installe les dépendances PyPI (une seule)
RUN pip install --no-cache-dir pandas pyphonetics unidecode tqdm

COPY load_dict.py .
